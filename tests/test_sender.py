"""P1 viết. Dùng channel/metrics giả để kiểm thử Sender độc lập."""
import pytest

from tcpfc.engine import Simulator
from tcpfc.segment import Ack
from tcpfc.sender import Sender


class FakeChannel:
    def __init__(self):
        self.sent = []

    def send_to_receiver(self, seg):
        self.sent.append(seg)


class NullMetrics:
    def __getattr__(self, name):
        return lambda *a, **k: None


def make(rwnd=4380, total=100_000, mss=1460):
    sim, ch = Simulator(), FakeChannel()
    s = Sender(sim, ch, NullMetrics(), total_bytes=total, mss=mss, rto=1.0, init_rwnd=rwnd)
    return sim, ch, s


def test_never_exceeds_rwnd():
    sim, ch, s = make(rwnd=4380)
    s.start()
    assert s.in_flight <= 4380
    assert len(ch.sent) == 3


def test_ack_slides_window():
    sim, ch, s = make(rwnd=4380)
    s.start()
    s.on_ack(Ack(ack=1460, rwnd=4380, sent_at=0.0))
    assert s.snd_una == 1460 and s.in_flight <= 4380 and len(ch.sent) == 4


def test_zero_window_stops_and_probes():
    sim, ch, s = make(rwnd=4380)
    s.start()
    s.on_ack(Ack(ack=4380, rwnd=0, sent_at=0.0))
    n = len(ch.sent)
    sim.run(until=5.0)
    probes = [x for x in ch.sent[n:] if x.is_probe]
    assert probes, "phải gửi window probe khi rwnd = 0"
    assert all(x.is_probe or x.is_retx for x in ch.sent[n:])


def test_timeout_retransmits_from_snd_una():
    sim, ch, s = make(rwnd=4380)
    s.start()
    sim.run(until=1.5)   # không có ACK -> RTO
    retx = [x for x in ch.sent if x.is_retx]
    assert retx and retx[0].seq == 0
