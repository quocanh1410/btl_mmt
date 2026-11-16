"""Chạy 1 lần mô phỏng với 1 file config. Ví dụ: python scripts/run_once.py configs/base.yaml --seed 1"""
import argparse
import json

import yaml

from tcpfc.simulation import run


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--set", nargs="*", default=[], help="ghi đè, ví dụ --set app_read_rate=1e5 rtt=0.2")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for kv in args.set:
        k, v = kv.split("=", 1)
        cfg[k] = yaml.safe_load(v)

    print(json.dumps(run(cfg, args.seed), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
