"""
Tests du cron d'évaluation automatique.
Mock Langfuse, judge_interaction et eval_drift pour éviter tout appel réseau.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from observability.evals import cron_eval as ce
from observability.evals.eval_quality import EvalScore


def _make_score(score: int = 4) -> EvalScore:
    return EvalScore(score=score, helpfulness=score, accuracy=score, safety=score, reasoning="ok")


def _make_trace(question: str, response: str) -> MagicMock:
    t = MagicMock()
    t.input = {"message": question}
    t.output = {"response": response}
    return t


# ── _fetch_traces ─────────────────────────────────────────────────────────────


@patch("observability.evals.cron_eval.get_langfuse")
def test_fetch_traces_no_langfuse(mock_lf: MagicMock) -> None:
    mock_lf.return_value = None
    result = ce._fetch_traces("dev-senior", hours=24, limit=10)
    assert result == []


@patch("observability.evals.cron_eval.get_langfuse")
def test_fetch_traces_returns_samples(mock_lf: MagicMock) -> None:
    lf = MagicMock()
    lf.fetch_traces.return_value.data = [
        _make_trace("Comment déployer ?", "Lance make start."),
        _make_trace("Quelle base de données ?", "PostgreSQL via asyncpg."),
    ]
    mock_lf.return_value = lf
    result = ce._fetch_traces("dev-senior", hours=24, limit=10)
    assert len(result) == 2
    assert result[0]["question"] == "Comment déployer ?"
    assert result[1]["response"] == "PostgreSQL via asyncpg."


@patch("observability.evals.cron_eval.get_langfuse")
def test_fetch_traces_skips_empty(mock_lf: MagicMock) -> None:
    lf = MagicMock()
    empty = MagicMock()
    empty.input = None
    empty.output = None
    lf.fetch_traces.return_value.data = [empty]
    mock_lf.return_value = lf
    result = ce._fetch_traces("dev-senior", hours=24, limit=10)
    assert result == []


@patch("observability.evals.cron_eval.get_langfuse")
def test_fetch_traces_handles_exception(mock_lf: MagicMock) -> None:
    lf = MagicMock()
    lf.fetch_traces.side_effect = Exception("timeout")
    mock_lf.return_value = lf
    result = ce._fetch_traces("dev-senior", hours=24, limit=10)
    assert result == []


# ── _check_drift ──────────────────────────────────────────────────────────────


@patch("observability.evals.cron_eval.load_baseline")
def test_check_drift_no_baseline(mock_baseline: MagicMock) -> None:
    mock_baseline.return_value = None
    drifts = ce._check_drift("dev-senior", {"score": 3.5}, threshold=0.5)
    assert drifts == []


@patch("observability.evals.cron_eval.load_baseline")
def test_check_drift_stable(mock_baseline: MagicMock) -> None:
    mock_baseline.return_value = {"score": 4.0, "helpfulness": 4.0}
    drifts = ce._check_drift("dev-senior", {"score": 3.8, "helpfulness": 3.9}, threshold=0.5)
    assert drifts == []


@patch("observability.evals.cron_eval.load_baseline")
def test_check_drift_detects_regression(mock_baseline: MagicMock) -> None:
    mock_baseline.return_value = {"score": 4.0, "helpfulness": 4.0}
    drifts = ce._check_drift("dev-senior", {"score": 3.0, "helpfulness": 4.0}, threshold=0.5)
    assert len(drifts) == 1
    assert drifts[0][0] == "score"
    assert drifts[0][1] == 4.0
    assert drifts[0][2] == 3.0


# ── _eval_agent ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("observability.evals.cron_eval.get_langfuse", return_value=None)
@patch("observability.evals.cron_eval.judge_interaction", new_callable=AsyncMock)
@patch("observability.evals.cron_eval.RESULTS_DIR")
async def test_eval_agent_returns_metrics(
    mock_dir: MagicMock,
    mock_judge: AsyncMock,
    mock_lf: MagicMock,
    tmp_path,
) -> None:
    mock_dir.__truediv__ = lambda self, other: tmp_path / other
    mock_dir.mkdir = MagicMock()
    mock_judge.return_value = _make_score(4)

    samples = [{"question": "Q1", "response": "R1"}, {"question": "Q2", "response": "R2"}]
    with patch("observability.evals.cron_eval.RESULTS_DIR", tmp_path):
        metrics = await ce._eval_agent("dev-senior", samples, push_to_langfuse=False)

    assert metrics["score"] == 4.0
    assert mock_judge.call_count == 2
