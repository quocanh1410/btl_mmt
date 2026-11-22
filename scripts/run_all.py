"""CHẠY TẤT CẢ BẰNG MỘT LỆNH:   python scripts/run_all.py

1. Chạy kiểm thử (pytest)
2. Chạy toàn bộ thí nghiệm (4 kịch bản + 5 nhóm quét tham số × 5 seed) -> results/
3. Vẽ biểu đồ -> plots/
4. Ghi thông tin môi trường chạy -> results/ENVIRONMENT.md
"""
from __future__ import annotations

import datetime as dt
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def step(title: str, args: list[str]) -> None:
    print(f"\n=== {title} ===", flush=True)
    r = subprocess.run([sys.executable, *args], cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"Lỗi ở bước: {title}")


def write_env() -> None:
    import matplotlib
    import numpy
    import pandas
    import yaml

    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                                text=True).stdout.strip() or "(không có git)"
    except OSError:
        commit = "(không có git)"
    text = f"""# Môi trường chạy thí nghiệm (tự sinh bởi scripts/run_all.py)

- Ngày chạy: {dt.datetime.now():%Y-%m-%d %H:%M}
- Hệ điều hành: {platform.platform()}
- CPU: {platform.processor() or platform.machine()}
- Python: {platform.python_version()}
- Thư viện: pandas {pandas.__version__}, numpy {numpy.__version__}, matplotlib {matplotlib.__version__}, pyyaml {yaml.__version__}
- Commit: {commit}
- Cấu hình: configs/base.yaml, configs/scenarios.yaml
"""
    (ROOT / "results" / "ENVIRONMENT.md").write_text(text, encoding="utf-8")


def main() -> None:
    step("1/3 Kiểm thử", ["-m", "pytest", "-q"])
    step("2/3 Chạy thí nghiệm", ["scripts/run_experiments.py"])
    step("3/3 Vẽ biểu đồ", ["scripts/plot_results.py"])
    write_env()
    print("\nXONG. Xem kết quả ở results/summary.csv và biểu đồ trong thư mục plots/")


if __name__ == "__main__":
    main()
