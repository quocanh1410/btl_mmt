"""Chạy 1 lần mô phỏng và in kết quả dễ đọc.

Ví dụ:
    python scripts/run_once.py                                   # cấu hình mặc định (base.yaml)
    python scripts/run_once.py --scenario S4_tam_dung --plot     # chạy kịch bản S4 và vẽ diễn biến
    python scripts/run_once.py --set app_read_rate=2e5 rtt=0.05 loss_rate=0.01 --seed 3
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tcpfc.simulation import run  # noqa: E402

LABELS = [
    ("goodput", "Goodput", lambda v: f"{v / 1000:.1f} kB/s  ({v * 8 / 1e6:.2f} Mbit/s)"),
    ("theory_goodput", "Giới hạn lý thuyết", lambda v: f"{v / 1000:.1f} kB/s"),
    ("bottleneck", "Nút cổ chai (lý thuyết)", str),
    ("completion_time", "Thời gian hoàn tất", lambda v: f"{v:.3f} s"),
    ("avg_in_flight", "Dữ liệu đang bay TB", lambda v: f"{v / 1024:.1f} KiB"),
    ("avg_buffer_pct", "Bộ đệm nhận bị chiếm TB", lambda v: f"{v:.1f} %"),
    ("zero_window_count", "Số lần rwnd = 0", str),
    ("zero_window_time", "Tổng thời gian rwnd = 0", lambda v: f"{v:.2f} s"),
    ("probe_count", "Số window probe", str),
    ("window_update_count", "Số window update", str),
    ("timeout_count", "Số lần timeout (RTO)", str),
    ("retx_bytes", "Byte gửi lại", str),
]


def parse_value(v: str):
    """'2e5' -> 200000.0, '1460' -> 1460, 'true' -> True, 'null' -> None."""
    for conv in (int, float):
        try:
            return conv(v)
        except ValueError:
            pass
    return yaml.safe_load(v)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "configs" / "base.yaml"))
    ap.add_argument("--scenario", help="tên kịch bản trong configs/scenarios.yaml, ví dụ S3_nang")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--set", nargs="*", default=[], help="ghi đè tham số, ví dụ --set app_read_rate=1e5 rtt=0.2")
    ap.add_argument("--plot", action="store_true", help="vẽ diễn biến theo thời gian -> plots/run_once.png")
    ap.add_argument("--json", action="store_true", help="in toàn bộ kết quả dạng JSON")
    a = ap.parse_args()

    with open(a.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if a.scenario:
        sc = yaml.safe_load(open(ROOT / "configs" / "scenarios.yaml", encoding="utf-8"))["scenarios"]
        cfg.update(sc[a.scenario])
    for kv in a.set:
        k, v = kv.split("=", 1)
        cfg[k] = parse_value(v)

    out = run(cfg, a.seed, return_timeseries=a.plot)
    if a.json:
        print(json.dumps({k: v for k, v in out.items() if k != "timeseries"}, indent=2, ensure_ascii=False))
    else:
        print(f"Tham số: B = {cfg['buffer_size']} B, RTT = {cfg['rtt'] * 1000:g} ms, R_app = "
              f"{float(cfg['app_read_rate']) / 1000:g} kB/s, mất gói = {float(cfg.get('loss_rate', 0)) * 100:g} %, "
              f"seed = {a.seed}")
        for key, label, fmt in LABELS:
            print(f"  {label:<26}: {fmt(out[key])}")

    if a.plot:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        ts = out["timeseries"]
        fig, ax = plt.subplots(figsize=(10, 4.5))
        for key, name, color, ls in (("in_flight", "Dữ liệu đang bay", "#2a78d6", "-"),
                                     ("rwnd", "rwnd quảng bá", "#eb6834", "--"),
                                     ("buffer", "Dữ liệu trong bộ đệm nhận", "#1baf7a", ":")):
            t = [p[0] for p in ts[key]]
            v = [p[1] / 1024 for p in ts[key]]
            ax.step(t, v, where="post", color=color, ls=ls, lw=1.8, label=name)
        ax.set_xlabel("Thời gian (s)")
        ax.set_ylabel("KiB")
        ax.set_title("Diễn biến theo thời gian")
        ax.legend()
        (ROOT / "plots").mkdir(exist_ok=True)
        fig.tight_layout()
        fig.savefig(ROOT / "plots" / "run_once.png", dpi=150)
        print("Đã lưu plots/run_once.png")


if __name__ == "__main__":
    main()
