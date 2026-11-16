"""Chạy toàn bộ kịch bản × seed, ghi CSV vào results/raw/. Chủ sở hữu: P3.

Đầu ra mong muốn:
- results/raw/<ten_kich_ban>.csv : mỗi dòng = 1 lần chạy (tham số + seed + chỉ tiêu)
- results/summary.csv            : gom theo (kịch bản, giá trị tham số) -> mean, std của từng chỉ tiêu
"""
import copy
from pathlib import Path

import yaml

from tcpfc.simulation import run

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(p: Path) -> dict:
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def expand(base: dict, spec: dict) -> list[tuple[str, dict]]:
    """Trả về danh sách (tên kịch bản con, config đầy đủ)."""
    # TODO(P3): xử lý 2 dạng:
    #  - kịch bản thường: base ghi đè bởi các khóa trong spec
    #  - sweep: với mỗi kịch bản trong base_on, mỗi giá trị trong values -> 1 config
    raise NotImplementedError


def main() -> None:
    base = load_yaml(ROOT / "configs" / "base.yaml")
    sc = load_yaml(ROOT / "configs" / "scenarios.yaml")
    seeds = sc["seeds"]
    # TODO(P3): lặp qua sc["scenarios"], expand, chạy run(cfg, seed) cho mọi seed,
    #           ghi CSV bằng pandas; tính mean/std -> results/summary.csv
    raise NotImplementedError


if __name__ == "__main__":
    main()
