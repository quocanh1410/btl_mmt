"""Ghép các khối và chạy một lần mô phỏng. Chủ sở hữu: P1."""

from __future__ import annotations

import random

from .channel import Channel
from .engine import Simulator
from .metrics import Metrics
from .receiver import Receiver
from .sender import Sender


def theory_goodput(config: dict) -> dict:
    """Giới hạn lý thuyết khi KHÔNG mất gói.

    - Giới hạn cửa sổ: mỗi RTT gửi được tối đa một cửa sổ đầy segment MSS
      -> floor(min(B, max_wnd) / MSS) · MSS / RTT
    - Giới hạn đường truyền: bandwidth · MSS / (MSS + 40)  (nếu có cấu hình băng thông)
    - Giới hạn bên nhận: tốc độ ứng dụng đọc R_app
    goodput lý thuyết = min(các giới hạn trên)
    """
    mss = int(config["mss"])
    w = int(config["buffer_size"])
    if config.get("max_wnd") is not None:
        w = min(w, int(config["max_wnd"]))
    window_limit = (w // mss) * mss / float(config["rtt"])
    app_limit = float(config["app_read_rate"])
    bw = config.get("bandwidth")
    link_limit = float(bw) / 8 * mss / (mss + 40) if bw else float("inf")
    limits = {"window": window_limit, "link": link_limit, "receiver_app": app_limit}
    return {
        "theory_window_limit": window_limit,
        "theory_link_limit": link_limit,
        "theory_app_limit": app_limit,
        "theory_goodput": min(limits.values()),
        "bottleneck": min(limits, key=limits.get),
    }


def run(config: dict, seed: int, return_timeseries: bool = False) -> dict:
    """Chạy 1 lần với config (dict từ YAML) và seed. Trả về chỉ tiêu + tham số + lý thuyết."""
    rng = random.Random(seed)
    sim = Simulator()

    total = int(config["total_bytes"])
    mss = int(config["mss"])
    buf = int(config["buffer_size"])
    if buf < mss:
        raise ValueError("buffer_size phải ≥ mss, nếu không bên gửi không bao giờ gửi được segment đầy")

    metrics = Metrics(total_bytes=total, buffer_size=buf)
    channel = Channel(
        sim,
        rtt=float(config["rtt"]),
        loss_rate=float(config.get("loss_rate", 0.0)),
        rng=rng,
        loss_on_ack=bool(config.get("loss_on_ack", True)),
        jitter=float(config.get("jitter", 0.0)),
        metrics=metrics,
        bandwidth=float(config["bandwidth"]) if config.get("bandwidth") else None,
    )
    sender = Sender(
        sim, channel, metrics,
        total_bytes=total, mss=mss,
        rto=float(config["rto"]),
        init_rwnd=buf,
        max_wnd=config.get("max_wnd"),
        persist_init=config.get("persist_init"),
        persist_max=float(config.get("persist_max", 60.0)),
        rto_backoff=bool(config.get("rto_backoff", True)),
    )
    receiver = Receiver(
        sim, channel, metrics,
        buffer_size=buf,
        app_read_rate=float(config["app_read_rate"]),
        app_read_interval=float(config["app_read_interval"]),
        total_bytes=total, mss=mss,
        store_out_of_order=bool(config.get("store_out_of_order", True)),
        sws_avoid=bool(config.get("rx_sws_avoid", True)),
        app_pause_at=config.get("app_pause_at"),
        app_pause_duration=float(config.get("app_pause_duration") or 0.0),
    )
    channel.connect(sender, receiver)

    receiver.start()
    sender.start()
    sim.run(until=float(config.get("max_sim_time", 3600.0)))

    out = {"seed": seed, **{k: v for k, v in config.items() if not isinstance(v, (dict, list))}}
    out.update(metrics.summary())
    out.update(theory_goodput(config))
    if return_timeseries:
        out["timeseries"] = metrics.timeseries()
    return out
