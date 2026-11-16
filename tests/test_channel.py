"""P3 viết thêm. Bỏ @pytest.mark.todo khi channel.py xong."""
import random

import pytest

from tcpfc.channel import Channel
from tcpfc.engine import Simulator
from tcpfc.segment import Segment


class _Sink:
    def __init__(self):
        self.got = []

    def on_segment(self, s):
        self.got.append(s)

    def on_ack(self, a):
        self.got.append(a)


@pytest.mark.todo
def test_delay_is_half_rtt():
    sim, sink = Simulator(), _Sink()
    ch = Channel(sim, rtt=0.2, loss_rate=0.0, rng=random.Random(1))
    ch.connect(sink, sink)
    ch.send_to_receiver(Segment(0, 100, 0.0))
    sim.run()
    assert len(sink.got) == 1 and sim.now == pytest.approx(0.1)


@pytest.mark.todo
def test_loss_rate_approx():
    sim, sink = Simulator(), _Sink()
    ch = Channel(sim, rtt=0.1, loss_rate=0.2, rng=random.Random(42))
    ch.connect(sink, sink)
    for i in range(10000):
        ch.send_to_receiver(Segment(i, 1, 0.0))
    sim.run()
    assert 0.77 < len(sink.got) / 10000 < 0.83


@pytest.mark.todo
def test_same_seed_reproducible():
    def once():
        sim, sink = Simulator(), _Sink()
        ch = Channel(sim, rtt=0.1, loss_rate=0.3, rng=random.Random(7))
        ch.connect(sink, sink)
        for i in range(200):
            ch.send_to_receiver(Segment(i, 1, 0.0))
        sim.run()
        return [s.seq for s in sink.got]
    assert once() == once()
