"""Kiểm tra tích hợp với các trường hợp có đáp án dự đoán được bằng lý thuyết (Bước 3 của đề)."""
from pathlib import Path

import pytest
import yaml

from tcpfc.simulation import run

BASE = yaml.safe_load((Path(__file__).resolve().parents[1] / "configs" / "base.yaml").read_text(encoding="utf-8"))


def cfg(**kw):
    c = dict(BASE)
    c.update(kw)
    return c


def test_all_bytes_delivered_no_loss():
    out = run(cfg(), seed=1)
    assert out["completed"]
    assert out["retx_bytes"] == 0 and out["timeout_count"] == 0


def test_window_limited_goodput_close_to_theory():
    # ứng dụng đọc rất nhanh, băng thông lớn -> goodput ≈ floor(B/MSS)·MSS / RTT (cận trên)
    out = run(cfg(app_read_rate=1e9, total_bytes=5_000_000), seed=1)
    assert out["bottleneck"] == "window"
    assert out["goodput"] <= out["theory_goodput"] * 1.001
    assert out["goodput"] == pytest.approx(out["theory_goodput"], rel=0.15)


def test_receiver_bottleneck_goodput_close_to_app_rate():
    out = run(cfg(app_read_rate=1e5), seed=1)
    assert out["bottleneck"] == "receiver_app"
    assert out["goodput"] == pytest.approx(1e5, rel=0.02)
    assert out["avg_buffer_pct"] > 50          # dữ liệu ứ lại ở bộ đệm nhận


def test_link_limited():
    out = run(cfg(app_read_rate=1e9, buffer_size=262144, bandwidth=1e7), seed=1)
    assert out["bottleneck"] == "link"
    assert out["goodput"] == pytest.approx(out["theory_goodput"], rel=0.1)


def test_app_pause_gives_zero_window_probe_and_update():
    out = run(cfg(app_read_rate=1e5, app_pause_at=1.0, app_pause_duration=5.0), seed=1)
    assert out["completed"]
    assert out["zero_window_count"] >= 1
    assert out["zero_window_time"] > 4.0        # rwnd = 0 gần suốt thời gian tạm dừng
    assert out["probe_count"] >= 2              # persist timer gửi probe, có backoff
    assert out["window_update_count"] >= 1      # ứng dụng đọc lại -> báo cửa sổ mới


def test_zero_window_when_app_rate_times_rtt_below_mss():
    # Ở trạng thái ổn định, dữ liệu đang bay ≈ R_app·RTT. Nếu < 1 MSS thì rwnd liên tục về 0.
    out = run(cfg(app_read_rate=1e5, rtt=0.01), seed=1)
    assert 1e5 * 0.01 < BASE["mss"]
    assert out["zero_window_count"] > 10


def test_all_bytes_delivered_with_loss():
    out = run(cfg(loss_rate=0.02), seed=3)
    assert out["completed"]
    assert out["timeout_count"] > 0


def test_same_seed_same_result():
    a = run(cfg(loss_rate=0.02), seed=7)
    b = run(cfg(loss_rate=0.02), seed=7)
    assert a["goodput"] == b["goodput"] and a["timeout_count"] == b["timeout_count"]


def test_buffer_never_overflows():
    out = run(cfg(app_read_rate=5e4, loss_rate=0.01), seed=2)
    assert out["max_buffer"] <= BASE["buffer_size"]
