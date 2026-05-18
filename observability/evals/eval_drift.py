"""
Détection de dérive comportementale des agents.

Compare les scores d'évaluation récents à une baseline.
Lance une alerte (console + fichier) si la qualité chute.

Usage :
    python -m observability.evals.eval_drift --agent dev-senior --threshold 0.5
"""
import json
from pathlib import Path
from statistics import mean

import typer
from rich.console import Console

app = typer.Typer()
console = Console()

EVALS_DIR = Path("observability/evals/results")
BASELINE_DIR = Path("observability/evals/baselines")


def load_scores(agent: str, last_n: int) -> list[dict]:
    """Charge les N derniers fichiers d'évaluation pour un agent."""
    files = sorted(EVALS_DIR.glob(f"{agent}_*.json"), reverse=True)[:last_n]
    scores = []
    for f in files:
        scores.extend(json.loads(f.read_text()))
    return scores


def load_baseline(agent: str) -> dict | None:
    baseline_file = BASELINE_DIR / f"{agent}_baseline.json"
    if not baseline_file.exists():
        return None
    return json.loads(baseline_file.read_text())


def save_baseline(agent: str, metrics: dict) -> None:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    (BASELINE_DIR / f"{agent}_baseline.json").write_text(
        json.dumps(metrics, indent=2)
    )


def compute_metrics(scores: list[dict]) -> dict:
    if not scores:
        return {}
    fields = ["score", "helpfulness", "accuracy", "safety"]
    return {f: mean(s[f] for s in scores) for f in fields if scores}


@app.command()
def detect(
    agent: str = typer.Option("dev-senior", help="Agent à surveiller"),
    last_n: int = typer.Option(5, help="Nombre de fichiers d'eval récents à comparer"),
    threshold: float = typer.Option(0.5, help="Seuil de chute acceptable (en points sur 5)"),
    set_baseline: bool = typer.Option(False, "--set-baseline", help="Définir la baseline actuelle"),
) -> None:
    """Détecte une dérive de qualité par rapport à la baseline."""
    scores = load_scores(agent, last_n)
    if not scores:
        console.print(f"[yellow]Aucun fichier d'éval trouvé pour '{agent}'.[/]")
        raise typer.Exit(0)

    current = compute_metrics(scores)

    if set_baseline:
        save_baseline(agent, current)
        console.print(f"[green]Baseline définie pour '{agent}' :[/]")
        for k, v in current.items():
            console.print(f"  {k}: {v:.2f}")
        raise typer.Exit(0)

    baseline = load_baseline(agent)
    if not baseline:
        console.print(f"[yellow]Aucune baseline pour '{agent}'. Lance avec --set-baseline d'abord.[/]")
        raise typer.Exit(1)

    console.print(f"\n[bold]Détection de dérive — {agent}[/]")
    console.print(f"{'Métrique':<15} {'Baseline':>10} {'Actuel':>10} {'Δ':>10} {'Statut':>10}")
    console.print("-" * 55)

    drifts = []
    for metric, base_val in baseline.items():
        curr_val = current.get(metric, 0.0)
        delta = curr_val - base_val
        status = "✓" if delta >= -threshold else "⚠ DÉRIVE"
        if delta < -threshold:
            drifts.append((metric, base_val, curr_val, delta))
        console.print(f"{metric:<15} {base_val:>10.2f} {curr_val:>10.2f} {delta:>+10.2f} {status:>10}")

    if drifts:
        console.print(f"\n[bold red]ALERTE : {len(drifts)} métrique(s) en dérive :[/]")
        for metric, base, curr, delta in drifts:
            console.print(f"  {metric}: {base:.2f} → {curr:.2f} ({delta:+.2f})")
        raise typer.Exit(2)
    else:
        console.print("\n[bold green]✓ Aucune dérive détectée.[/]")


if __name__ == "__main__":
    app()
