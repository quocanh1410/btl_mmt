"""Chạy toàn bộ kịch bản × seed, ghi kết quả. Chủ sở hữu: P3.

Đầu ra:
- results/raw/<nhom>.csv           : mỗi dòng = 1 lần chạy (tham số + seed + chỉ tiêu + lý thuyết)
- results/summary.csv               : gom theo (nhóm, kịch bản, giá trị tham số) -> mean, std
- results/raw/timeseries_<kb>.csv   : chuỗi thời gian 1 lần chạy (seed đầu) của S3 và S4
Dùng:  python scripts/run_experiments.py   [--quick]  (--quick: 2 seed, để thử nhanh)
"""
from __future__ import annotations

import argparse
import copy
import sys
import time
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tcpfc.simulation import run  # noqa: E402

METRICS = ["goodput", "goodput_mbps", "completion_time", "avg_in_flight", "avg_buffer", "avg_buffer_pct",
           "max_buffer", "zero_window_count", "zero_window_time", "timeout_count", "probe_count",
           "window_update_count", "retx_bytes", "theory_goodput"]


def load_yaml(p: Path) -> dict:
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


def expand(base: dict, spec: dict) -> list[dict]:
    """Trả về danh sách job: {group, scenario, param, value, config}."""
    jobs = []
    for name, over in spec["scenarios"].items():
        cfg = copy.deepcopy(base)
        cfg.update(over or {})
        jobs.append(dict(group="scenarios", scenario=name, param="", value=None, config=cfg))
    for sweep, sw in (spec.get("sweeps") or {}).items():
        for sc in sw["base_on"]:
            for v in sw["values"]:
                cfg = copy.deepcopy(base)
                cfg.update(spec["scenarios"][sc] or {})
                cfg[sw["param"]] = v
                jobs.append(dict(group=sweep, scenario=sc, param=sw["param"], value=v, config=cfg))
    return jobs


def save_timeseries(cfg: dict, seed: int, path: Path) -> None:
    out = run(cfg, seed, return_timeseries=True)
    rows = []
    for key, series in out["timeseries"].items():
        if key == "events":
            rows += [{"series": f"event:{name}", "time_s": t, "value": 0} for t, name in series]
        else:
            rows += [{"series": key, "time_s": t, "value": v} for t, v in series]
    pd.DataFrame(rows).to_csv(path, index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="chỉ chạy 2 seed")
    args = ap.parse_args()

    base = load_yaml(ROOT / "configs" / "base.yaml")
    spec = load_yaml(ROOT / "configs" / "scenarios.yaml")
    seeds = spec["seeds"][:2] if args.quick else spec["seeds"]
    raw_dir = ROOT / "results" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    jobs = expand(base, spec)
    print(f"{len(jobs)} cấu hình × {len(seeds)} seed = {len(jobs) * len(seeds)} lần chạy")
    t0 = time.time()
    rows = []
    for i, job in enumerate(jobs, 1):
        for seed in seeds:
            r = run(job["config"], seed)
            r.update(group=job["group"], scenario=job["scenario"], param=job["param"], value=job["value"])
            rows.append(r)
        if i % 10 == 0 or i == len(jobs):
            print(f"  {i}/{len(jobs)} cấu hình  ({time.time() - t0:.1f}s)")

    df = pd.DataFrame(rows)
    for group, g in df.groupby("group"):
        g.to_csv(raw_dir / f"{group}.csv", index=False)

    agg = (df.groupby(["group", "scenario", "param", "value"], dropna=False)[METRICS]
             .agg(["mean", "std"]))
    agg.columns = [f"{m}_{s}" for m, s in agg.columns]
    agg = agg.reset_index()
    agg["n_seeds"] = len(seeds)
    agg.to_csv(ROOT / "results" / "summary.csv", index=False)

    for sc in ("S3_nang", "S4_tam_dung"):
        cfg = copy.deepcopy(base)
        cfg.update(spec["scenarios"][sc])
        save_timeseries(cfg, seeds[0], raw_dir / f"timeseries_{sc}.csv")

    not_done = df[~df["completed"]]
    if len(not_done):
        print(f"CẢNH BÁO: {len(not_done)} lần chạy chưa hoàn tất trong max_sim_time")
    print(f"Xong trong {time.time() - t0:.1f}s -> results/summary.csv, results/raw/")


if __name__ == "__main__":
    main()
