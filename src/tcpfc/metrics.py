"""Ghi log và tính chỉ tiêu. Chủ sở hữu: P2.

Định nghĩa chỉ tiêu (đưa vào báo cáo, mục Thiết kế thí nghiệm):
- completion_time (s)        = thời điểm ứng dụng nhận đọc xong byte cuối cùng
- goodput (byte/s)           = total_bytes / completion_time   (goodput_mbps = goodput·8/10^6)
- avg_in_flight (byte)       = trung bình THEO THỜI GIAN của snd_nxt − snd_una
- avg_buffer, max_buffer     = trung bình theo thời gian / cực đại của byte trong bộ đệm nhận
- avg_buffer_pct             = avg_buffer / B · 100 (%)
- zero_window_count          = số lần rwnd chuyển về 0;  zero_window_time (s) = tổng thời gian rwnd = 0
- timeout_count, probe_count, window_update_count, retx_bytes, data_lost, ack_lost
Trung bình theo thời gian của hàm bậc thang: sum(v_i · (t_{i+1} − t_i)) / T.
"""

from __future__ import annotations

import math
from collections import Counter

from .segment import Ack, Segment


class Metrics:
    def __init__(self, total_bytes: int, buffer_size: int) -> None:
        self.total_bytes = total_bytes
        self.buffer_size = buffer_size
        self.events: Counter[str] = Counter()
        self.ts_in_flight: list[tuple[float, int]] = [(0.0, 0)]
        self.ts_buffer: list[tuple[float, int]] = [(0.0, 0)]
        self.ts_rwnd: list[tuple[float, int]] = [(0.0, buffer_size)]
        self.ts_delivered: list[tuple[float, int]] = [(0.0, 0)]
        self.bytes_sent = 0
        self.retx_bytes = 0
        self.delivered = 0
        self.completion_time: float | None = None
        self.last_time = 0.0
        self.event_log: list[tuple[float, str]] = []   # (thời điểm, tên sự kiện)

    # ----------------------------------------------------- hàm ghi (module khác gọi)
    @staticmethod
    def _push(series: list[tuple[float, int]], t: float, v: int) -> None:
        if series and series[-1][0] == t:
            series[-1] = (t, v)          # cùng thời điểm: giữ giá trị cuối
        elif not series or series[-1][1] != v:
            series.append((t, v))

    def _tick(self, t: float) -> None:
        self.last_time = max(self.last_time, t)

    def on_send(self, t: float, seg: Segment, in_flight: int | None = None) -> None:
        self._tick(t)
        self.bytes_sent += seg.length
        if seg.is_retx:
            self.retx_bytes += seg.length
        if in_flight is not None:
            self._push(self.ts_in_flight, t, in_flight)

    def on_ack_received(self, t: float, ack: Ack, in_flight: int) -> None:
        self._tick(t)
        self._push(self.ts_in_flight, t, in_flight)

    def on_in_flight(self, t: float, in_flight: int) -> None:
        self._tick(t)
        self._push(self.ts_in_flight, t, in_flight)

    def on_buffer_change(self, t: float, buffered_bytes: int, rwnd: int) -> None:
        self._tick(t)
        self._push(self.ts_buffer, t, buffered_bytes)
        self._push(self.ts_rwnd, t, rwnd)

    def on_app_read(self, t: float, nbytes: int) -> None:
        self._tick(t)
        self.delivered += nbytes
        self._push(self.ts_delivered, t, self.delivered)
        if self.completion_time is None and self.delivered >= self.total_bytes:
            self.completion_time = t

    def on_event(self, t: float, name: str) -> None:
        self._tick(t)
        self.events[name] += 1
        self.event_log.append((t, name))

    # ----------------------------------------------------- tính chỉ tiêu
    @staticmethod
    def time_weighted_mean(series: list[tuple[float, int]], t_end: float) -> float:
        if t_end <= 0 or not series:
            return 0.0
        total = 0.0
        for i, (t, v) in enumerate(series):
            if t >= t_end:
                break
            t_next = series[i + 1][0] if i + 1 < len(series) else t_end
            total += v * (min(t_next, t_end) - t)
        return total / t_end

    @staticmethod
    def time_at_value(series: list[tuple[float, int]], value: int, t_end: float) -> float:
        tot = 0.0
        for i, (t, v) in enumerate(series):
            if t >= t_end:
                break
            t_next = series[i + 1][0] if i + 1 < len(series) else t_end
            if v == value:
                tot += min(t_next, t_end) - t
        return tot

    def summary(self) -> dict:
        done = self.completion_time is not None
        t_end = self.completion_time if done else self.last_time
        goodput = self.total_bytes / self.completion_time if done and self.completion_time > 0 else math.nan
        avg_buf = self.time_weighted_mean(self.ts_buffer, t_end)
        return {
            "completed": done,
            "completion_time": self.completion_time if done else math.nan,
            "goodput": goodput,
            "goodput_mbps": goodput * 8 / 1e6,
            "avg_in_flight": self.time_weighted_mean(self.ts_in_flight, t_end),
            "max_in_flight": max(v for _, v in self.ts_in_flight),
            "avg_buffer": avg_buf,
            "avg_buffer_pct": 100.0 * avg_buf / self.buffer_size,
            "max_buffer": max(v for _, v in self.ts_buffer),
            "zero_window_count": self.events["zero_window"],
            "zero_window_time": self.time_at_value(self.ts_rwnd, 0, t_end),
            "timeout_count": self.events["timeout"],
            "probe_count": self.events["probe"],
            "window_update_count": self.events["window_update"],
            "sender_blocked_count": self.events["sender_blocked"],
            "data_lost": self.events["data_lost"],
            "ack_lost": self.events["ack_lost"],
            "bytes_sent": self.bytes_sent,
            "retx_bytes": self.retx_bytes,
        }

    def timeseries(self) -> dict[str, list[tuple[float, int]]]:
        return {
            "in_flight": self.ts_in_flight,
            "buffer": self.ts_buffer,
            "rwnd": self.ts_rwnd,
            "delivered": self.ts_delivered,
            "events": self.event_log,
        }
