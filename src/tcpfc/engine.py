"""Bộ lập lịch sự kiện rời rạc. Chủ sở hữu: P3.

Bản khởi đầu đã chạy được để P1/P2 code song song. P3 chịu trách nhiệm kiểm thử,
mở rộng (ví dụ: log sự kiện, giới hạn số sự kiện để tránh vòng lặp vô hạn).
"""

from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(order=True)
class EventHandle:
    time: float
    order: int
    callback: Callable[..., Any] = field(compare=False)
    args: tuple = field(compare=False, default=())
    cancelled: bool = field(compare=False, default=False)


class Simulator:
    def __init__(self) -> None:
        self.now: float = 0.0
        self._queue: list[EventHandle] = []
        self._counter = itertools.count()  # phá hòa khi trùng thời điểm: FIFO

    def schedule(self, delay: float, callback: Callable[..., Any], *args: Any) -> EventHandle:
        if delay < 0:
            raise ValueError("delay phải >= 0")
        ev = EventHandle(self.now + delay, next(self._counter), callback, args)
        heapq.heappush(self._queue, ev)
        return ev

    def cancel(self, handle: EventHandle | None) -> None:
        if handle is not None:
            handle.cancelled = True

    def run(self, until: float | None = None, max_events: int = 10_000_000) -> None:
        n = 0
        while self._queue:
            ev = self._queue[0]
            if until is not None and ev.time > until:
                self.now = until
                return
            heapq.heappop(self._queue)
            if ev.cancelled:
                continue
            self.now = ev.time
            ev.callback(*ev.args)
            n += 1
            if n >= max_events:
                raise RuntimeError("Vượt quá max_events – nghi vòng lặp vô hạn")

    def stop(self) -> None:
        self._queue.clear()
