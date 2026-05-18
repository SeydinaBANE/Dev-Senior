"""
Store de métriques en mémoire — fenêtre glissante des 1000 dernières requêtes.

Réinitialisé au redémarrage du process (suffisant pour du monitoring temps réel).
Thread-safe via un verrou par agent.
"""
import threading
from collections import deque
from statistics import quantiles
from typing import TypedDict

_WINDOW = 1000  # nombre de latences conservées par agent


class AgentMetrics(TypedDict):
    requests_total: int
    errors_total: int
    error_rate: float
    latency_p50_ms: float
    latency_p95_ms: float


class _AgentStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests = 0
        self._errors = 0
        self._latencies: deque[float] = deque(maxlen=_WINDOW)

    def record(self, latency_ms: float, error: bool = False) -> None:
        with self._lock:
            self._requests += 1
            if error:
                self._errors += 1
            self._latencies.append(latency_ms)

    def snapshot(self) -> AgentMetrics:
        with self._lock:
            reqs = self._requests
            errs = self._errors
            lats = list(self._latencies)

        if lats:
            qs = quantiles(lats, n=100)
            p50 = round(qs[49], 1)
            p95 = round(qs[94], 1)
        else:
            p50 = p95 = 0.0

        return AgentMetrics(
            requests_total=reqs,
            errors_total=errs,
            error_rate=round(errs / reqs, 4) if reqs else 0.0,
            latency_p50_ms=p50,
            latency_p95_ms=p95,
        )


_stores: dict[str, _AgentStore] = {
    "dev-senior": _AgentStore(),
    "biz-manager": _AgentStore(),
}


def record_request(agent: str, latency_ms: float, error: bool = False) -> None:
    if agent in _stores:
        _stores[agent].record(latency_ms, error)


def get_metrics(agent: str) -> AgentMetrics | None:
    store = _stores.get(agent)
    return store.snapshot() if store else None


def get_all_metrics() -> dict[str, AgentMetrics]:
    return {agent: store.snapshot() for agent, store in _stores.items()}
