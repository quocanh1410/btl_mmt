"""Ghép các khối và chạy một lần mô phỏng. Chủ sở hữu: P1."""

from __future__ import annotations

import random

from .channel import Channel
from .engine import Simulator
from .metrics import Metrics
from .receiver import Receiver
from .sender import Sender


def run(config: dict, seed: int, return_timeseries: bool = False) -> dict:
    """Chạy 1 lần với config (dict từ YAML) và seed. Trả về chỉ tiêu + tham số."""
    rng = random.Random(seed)
    sim = Simulator()

    total = int(config["total_bytes"])
    mss = int(config["mss"])
    buf = int(config["buffer_size"])

    metrics = Metrics(total_bytes=total, buffer_size=buf)
    channel = Channel(
        sim,
        rtt=float(config["rtt"]),
        loss_rate=float(config.get("loss_rate", 0.0)),
        rng=rng,
        loss_on_ack=bool(config.get("loss_on_ack", True)),
        jitter=float(config.get("jitter", 0.0)),
        metrics=metrics,
    )
    sender = Sender(
        sim, channel, metrics,
        total_bytes=total, mss=mss,
        rto=float(config["rto"]),
        init_rwnd=buf,
        max_wnd=config.get("max_wnd"),
    )
    receiver = Receiver(
        sim, channel, metrics,
        buffer_size=buf,
        app_read_rate=float(config["app_read_rate"]),
        app_read_interval=float(config["app_read_interval"]),
        total_bytes=total, mss=mss,
        store_out_of_order=bool(config.get("store_out_of_order", True)),
    )
    channel.connect(sender, receiver)

    receiver.start()
    sender.start()
    sim.run(until=float(config.get("max_sim_time", 3600.0)))

    out = {"seed": seed, **{k: v for k, v in config.items() if not isinstance(v, (dict, list))}}
    out.update(metrics.summary())
    if return_timeseries:
        out["timeseries"] = metrics.timeseries()
    return out
