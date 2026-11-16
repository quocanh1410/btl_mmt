"""P2 viết."""
import pytest

from tcpfc.engine import Simulator
from tcpfc.receiver import Receiver
from tcpfc.segment import Segment


class FakeChannel:
    def __init__(self):
        self.acks = []

    def send_to_sender(self, ack):
        self.acks.append(ack)


class NullMetrics:
    def __getattr__(self, name):
        return lambda *a, **k: None


def make(buf=4380, rate=0.0, interval=0.1, total=100_000):
    sim, ch = Simulator(), FakeChannel()
    r = Receiver(sim, ch, NullMetrics(), buffer_size=buf, app_read_rate=rate,
                 app_read_interval=interval, total_bytes=total, mss=1460)
    return sim, ch, r


@pytest.mark.todo
def test_rwnd_decreases_as_buffer_fills():
    sim, ch, r = make()
    r.on_segment(Segment(0, 1460, 0.0))
    assert ch.acks[-1].ack == 1460 and ch.acks[-1].rwnd == 4380 - 1460


@pytest.mark.todo
def test_zero_window_when_full_and_app_not_reading():
    sim, ch, r = make()
    for i in range(3):
        r.on_segment(Segment(i * 1460, 1460, 0.0))
    assert ch.acks[-1].rwnd == 0


@pytest.mark.todo
def test_window_update_after_app_read():
    sim, ch, r = make(rate=14600, interval=0.1)   # đọc 1460 byte mỗi 0.1 s
    for i in range(3):
        r.on_segment(Segment(i * 1460, 1460, 0.0))
    r.start()
    sim.run(until=0.15)
    assert any(a.is_window_update and a.rwnd >= 1460 for a in ch.acks)


@pytest.mark.todo
def test_out_of_order_then_fill_gap():
    sim, ch, r = make(buf=10_000)
    r.on_segment(Segment(1460, 1460, 0.0))
    assert ch.acks[-1].ack == 0            # ACK trùng
    r.on_segment(Segment(0, 1460, 0.0))
    assert ch.acks[-1].ack == 2920         # lấp chỗ trống
