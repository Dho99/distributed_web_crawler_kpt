from __future__ import annotations

import platform
import time
from collections import deque

import psutil

from shared.models import WorkerMetrics


class ResourceMonitor:
    """Samples real host resources; child process count proves multiprocessing."""

    def __init__(self, pool_size: int, capacity: int) -> None:
        self.pool_size = pool_size
        self.capacity = capacity
        self._process = psutil.Process()
        self._cpu_primed = False
        self._done_times: deque[float] = deque(maxlen=200)
        self._proc_times: deque[float] = deque(maxlen=200)
        psutil.cpu_percent(interval=None)
        self._cpu_primed = True

    def note_page(self, processing_ms: float) -> None:
        now = time.monotonic()
        self._done_times.append(now)
        self._proc_times.append(processing_ms)

    def throughput(self, window_s: float = 10.0) -> float:
        if not self._done_times:
            return 0.0
        now = time.monotonic()
        recent = [t for t in self._done_times if now - t <= window_s]
        if not recent:
            return 0.0
        return round(len(recent) / window_s, 3)

    def avg_processing_ms(self) -> float:
        if not self._proc_times:
            return 0.0
        return round(sum(self._proc_times) / len(self._proc_times), 1)

    def child_processes(self) -> int:
        try:
            return len(self._process.children(recursive=True))
        except psutil.Error:
            return 0

    def sample(self, inflight: int, active_tasks: int) -> WorkerMetrics:
        memory = psutil.virtual_memory()
        return WorkerMetrics(
            cpu_usage=psutil.cpu_percent(interval=None),
            memory_usage=memory.percent,
            memory_used=memory.used,
            active_processes=self.pool_size,
            child_processes=self.child_processes(),
            active_tasks=active_tasks,
            pending_tasks=0,
            inflight=inflight,
            capacity=self.capacity,
            throughput=self.throughput(),
            avg_processing_ms=self.avg_processing_ms(),
        )

    @staticmethod
    def hardware() -> dict:
        memory = psutil.virtual_memory()
        return {
            "cpu_cores": psutil.cpu_count(logical=True) or 1,
            "memory_total": memory.total,
            "os_name": f"{platform.system()} {platform.release()}",
            "python_version": platform.python_version(),
        }
