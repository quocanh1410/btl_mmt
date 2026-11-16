# Hợp đồng giao diện giữa các module

Mục đích: 4 người code song song mà ghép không vỡ. **Sửa file này hoặc `segment.py` phải qua PR và được cả 4 người approve.**

## Đơn vị
- Thời gian: **giây** (`float`). Kích thước: **byte** (`int`). Tốc độ: **byte/giây** trong code; chỉ đổi sang Mbit/s/KB/s khi vẽ.

## Dữ liệu dùng chung (`segment.py`)
```python
Segment(seq: int, length: int, sent_at: float, is_probe: bool = False, is_retx: bool = False)
Ack(ack: int, rwnd: int, sent_at: float, is_window_update: bool = False)
```
`ack` = số thứ tự byte tiếp theo bên nhận mong đợi (ACK tích lũy, như TCP).

## Engine (P3)
```python
sim.now -> float
sim.schedule(delay, callback, *args) -> EventHandle
sim.cancel(handle)
sim.run(until: float | None = None)
```

## Channel (P3)
```python
Channel(sim, rtt, loss_rate, rng, loss_on_ack=True, jitter=0.0)
channel.send_to_receiver(segment)   # sau RTT/2 gọi receiver.on_segment(segment) nếu không mất
channel.send_to_sender(ack)         # sau RTT/2 gọi sender.on_ack(ack) nếu không mất
channel.connect(sender, receiver)
```

## Sender (P1)
```python
Sender(sim, channel, metrics, total_bytes, mss, rto, init_rwnd, max_wnd=None)
sender.start()
sender.on_ack(ack)
sender.done -> bool                 # True khi snd_una == total_bytes
```

## Receiver (P2)
```python
Receiver(sim, channel, metrics, buffer_size, app_read_rate, app_read_interval, total_bytes)
receiver.start()                    # bắt đầu sự kiện ứng dụng đọc định kỳ
receiver.on_segment(segment)
receiver.rwnd -> int
receiver.delivered_bytes -> int     # byte ứng dụng đã đọc
```

## Metrics (P2)
Các module **chỉ gọi** các hàm ghi; P2 tính chỉ tiêu trong metrics.py.
```python
metrics.on_send(t, segment)
metrics.on_ack_received(t, ack, in_flight)
metrics.on_buffer_change(t, buffered_bytes, rwnd)
metrics.on_app_read(t, nbytes)
metrics.on_event(t, name)           # "zero_window", "probe", "timeout", "window_update"...
metrics.summary() -> dict           # goodput, completion_time, avg_in_flight, ...
metrics.timeseries() -> dict[str, list]
```

## Simulation (P1)
```python
run(config: dict, seed: int) -> dict   # trả về metrics.summary() + tham số đầu vào
```
