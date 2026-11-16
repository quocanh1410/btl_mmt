"""P1 viết – kiểm tra tích hợp với các trường hợp có đáp án dự đoán được (Bước 3 của đề)."""
import pytest
import yaml
from pathlib import Path

from tcpfc.simulation import run

BASE = yaml.safe_load((Path(__file__).resolve().parents[1] / "configs" / "base.yaml").read_text(encoding="utf-8"))


@pytest.mark.todo
def test_all_bytes_delivered_no_loss():
    out = run(dict(BASE), seed=1)
    assert out["completion_time"] is not None


@pytest.mark.todo
def test_window_limited_goodput_close_to_theory():
    # app đọc rất nhanh -> goodput ≈ buffer/RTT
    cfg = dict(BASE, app_read_rate=1e9, total_bytes=5_000_000)
    out = run(cfg, seed=1)
    assert out["goodput"] == pytest.approx(cfg["buffer_size"] / cfg["rtt"], rel=0.15)


@pytest.mark.todo
def test_receiver_bottleneck_goodput_close_to_app_rate():
    cfg = dict(BASE, app_read_rate=1e5)
    out = run(cfg, seed=1)
    assert out["goodput"] == pytest.approx(1e5, rel=0.1)
    assert out["zero_window_count"] > 0


@pytest.mark.todo
def test_all_bytes_delivered_with_loss():
    out = run(dict(BASE, loss_rate=0.02), seed=3)
    assert out["completion_time"] is not None
