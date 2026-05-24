"""
Évaluation automatique quotidienne des agents.

Récupère les traces Langfuse des dernières 24h, évalue via LLM-as-judge,
détecte les dérives et sauvegarde un rapport quotidien.

Usage :
    python -m observability.evals.cron_eval
    python -m observability.evals.cron_eval --hours 48 --limit 30
    python -m observability.evals.cron_eval --dry-run

Planification launchd :
    make install-eval-cron
"""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import typer
from rich.console import Console

from observability.evals.eval_drift import (
    compute_metrics,
    load_baseline,
)
from observability.evals.eval_quality import EVALS_DIR, judge_interaction
from observability.langfuse_config import get_langfuse

app = typer.Typer()
console = Console()

AGENTS = ["dev-senior", "biz-manager"]
RESULTS_DIR = EVALS_DIR
LOG_DIR = Path("logs")


def _fetch_traces(agent: str, hours: int, limit: int) -> list[dict]:
    """Récupère les traces Langfuse récentes et les convertit en samples."""
    lf = get_langfuse()
    if lf is None:
        console.print(f"[yellow]Langfuse non configuré — pas de traces pour '{agent}'.[/]")
        return []
    try:
        since = datetime.now(UTC) - timedelta(hours=hours)
        traces = lf.fetch_traces(
            name=f"{agent}-chat",
            from_timestamp=since,
            limit=limit,
        )
        samples = []
        for trace in traces.data:
            if not trace.input or not trace.output:
                continue
            question = (
                trace.input.get("message", "")
                if isinstance(trace.input, dict)
                else str(trace.input)
            )
            response = (
                trace.output.get("response", "")
                if isinstance(trace.output, dict)
                else str(trace.output)
            )
            if question and response:
                samples.append({"question": question, "response": response})
        console.print(f"  {len(samples)} traces récupérées pour '{agent}'.")
        return samples
    except Exception as e:
        console.print(f"[yellow]Erreur Langfuse pour '{agent}' : {e}[/]")
        return []


async def _eval_agent(
    agent: str,
    samples: list[dict],
    push_to_langfuse: bool,
) -> dict:
    """Évalue un agent et retourne ses métriques."""
    lf = get_langfuse() if push_to_langfuse else None
    scores = []

    for i, sample in enumerate(samples, 1):
        console.print(f"  [{agent}] sample {i}/{len(samples)}...")
        score = await judge_interaction(sample["question"], sample["response"])
        scores.append(score)

        if lf:
            trace = lf.trace(
                name=f"{agent}-eval",
                input={"question": sample["question"]},
                output={"response": sample["response"]},
                metadata={"agent": agent, "eval_run": True, "cron": True},
            )
            for metric in ["score", "helpfulness", "accuracy", "safety"]:
                trace.score(name=metric, value=getattr(score, metric) / 5.0)

    # Sauvegarde locale
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    output = RESULTS_DIR / f"{agent}_{timestamp}.json"
    output.write_text(json.dumps([s.model_dump() for s in scores], ensure_ascii=False, indent=2))

    return compute_metrics([s.model_dump() for s in scores])


def _check_drift(agent: str, current: dict, threshold: float) -> list[tuple]:
    """Retourne la liste des métriques en dérive."""
    baseline = load_baseline(agent)
    if not baseline:
        console.print(
            f"  [yellow]Pas de baseline pour '{agent}' — en définir une avec make eval-set-baseline.[/]"
        )
        return []
    drifts = []
    for metric, base_val in baseline.items():
        curr_val = current.get(metric, 0.0)
        if curr_val - base_val < -threshold:
            drifts.append((metric, base_val, curr_val))
    return drifts


def _write_daily_log(report: dict) -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    log_path = LOG_DIR / f"eval_{date}.log"
    log_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return log_path


@app.command()
def run(
    hours: int = typer.Option(24, help="Fenêtre de temps pour récupérer les traces (en heures)"),
    limit: int = typer.Option(20, help="Nombre max de traces par agent"),
    threshold: float = typer.Option(0.5, help="Seuil de dérive acceptable (en points sur 5)"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Sans push Langfuse ni écriture de fichiers"
    ),
) -> None:
    """Évaluation automatique quotidienne — à lancer via launchd ou make run-eval-cron."""
    started_at = datetime.now(UTC).isoformat()
    console.print(f"\n[bold]Évaluation automatique — {started_at[:10]}[/]\n")

    report: dict = {"started_at": started_at, "agents": {}}
    all_drifts: list[str] = []

    async def run_all() -> None:
        for agent in AGENTS:
            console.print(f"[cyan]Agent : {agent}[/]")
            samples = _fetch_traces(agent, hours, limit)
            if not samples:
                console.print(f"  [yellow]Aucun sample — agent '{agent}' ignoré.[/]")
                report["agents"][agent] = {"skipped": True, "reason": "no_samples"}
                continue

            metrics = await _eval_agent(agent, samples, push_to_langfuse=not dry_run)
            drifts = _check_drift(agent, metrics, threshold)

            report["agents"][agent] = {
                "samples_evaluated": len(samples),
                "metrics": metrics,
                "drifts": [{"metric": m, "baseline": b, "current": c} for m, b, c in drifts],
            }

            if drifts:
                all_drifts.append(agent)
                console.print(f"  [bold red]DÉRIVE détectée sur {len(drifts)} métrique(s).[/]")
                for metric, base, curr in drifts:
                    console.print(f"    {metric}: {base:.2f} → {curr:.2f} ({curr - base:+.2f})")
            else:
                console.print(
                    f"  [green]✓ Qualité stable. Score moyen : {metrics.get('score', 0):.2f}/5[/]"
                )

    asyncio.run(run_all())

    report["finished_at"] = datetime.now(UTC).isoformat()
    report["drifts_detected"] = all_drifts

    if not dry_run:
        log_path = _write_daily_log(report)
        console.print(f"\n[green]Rapport sauvegardé : {log_path}[/]")

    if all_drifts:
        console.print(f"\n[bold red]ALERTE : dérive sur {', '.join(all_drifts)}[/]")
        raise typer.Exit(2)

    console.print("\n[bold green]✓ Évaluation terminée sans dérive.[/]")


if __name__ == "__main__":
    app()
