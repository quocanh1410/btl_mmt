# ET4230 – Đề 09: TCP Flow Control (Sliding Window & Receiver Window)

Mô phỏng sự kiện rời rạc (discrete-event) bên gửi / bên nhận TCP ở mức trừu tượng:
sequence/ACK tích lũy, bộ đệm nhận, **advertised window (rwnd)**, hành vi khi bộ đệm đầy
(zero window + persist/probe). Mục tiêu chính: minh họa và đo **phía nhận trở thành nút cổ chai**.

> ⚠️ Đề này là **flow control**, KHÔNG phải congestion control. Mô hình không có `cwnd`,
> slow start, fast retransmit… Cửa sổ gửi chỉ bị giới hạn bởi `rwnd` (và tùy chọn một hằng số `max_wnd`).

## Thành viên & phân công (tóm tắt — chi tiết ở [docs/PHAN_CONG.md](docs/PHAN_CONG.md))

| Mã | Thành viên | Vai trò chính | Thư mục / file sở hữu |
|----|-----------|---------------|------------------------|
| P1 | _(điền tên – MSSV)_ | Trưởng nhóm, **Bên gửi** + tích hợp | `src/tcpfc/sender.py`, `src/tcpfc/simulation.py` |
| P2 | _(điền tên – MSSV)_ | **Bên nhận**, bộ đệm, rwnd, ứng dụng đọc | `src/tcpfc/receiver.py` |
| P3 | _(điền tên – MSSV)_ | **Kênh truyền**, engine sự kiện, kiểm chứng TCP thật (Wireshark) | `src/tcpfc/engine.py`, `src/tcpfc/channel.py`, `demo/` |
| P4 | _(điền tên – MSSV)_ | **Thí nghiệm, chỉ tiêu, biểu đồ**, tổng hợp báo cáo | `src/tcpfc/metrics.py`, `scripts/`, `configs/`, `plots/` |

## Cấu trúc thư mục

```
.
├── src/tcpfc/          # mã nguồn mô phỏng (package Python)
│   ├── engine.py       # bộ lập lịch sự kiện (P3)
│   ├── channel.py      # kênh: trễ một chiều, mất gói (P3)
│   ├── segment.py      # cấu trúc Segment / Ack dùng chung (cả nhóm – sửa phải qua PR)
│   ├── sender.py       # bên gửi: sliding window, RTO, persist timer (P1)
│   ├── receiver.py     # bên nhận: buffer, rwnd, app read (P2)
│   ├── metrics.py      # ghi log & tính chỉ tiêu (P4)
│   └── simulation.py   # ghép các khối, chạy 1 lần mô phỏng (P1)
├── configs/            # kịch bản YAML (P4)
├── scripts/            # chạy hàng loạt, vẽ biểu đồ (P4)
├── tests/              # kiểm thử pytest (mỗi người viết test cho module của mình)
├── results/raw/        # CSV/JSON kết quả thô (sinh tự động, có commit bản cuối)
├── plots/              # biểu đồ PNG/PDF (sinh tự động)
├── report/             # báo cáo: mỗi người 1 file section, P4 ghép
├── demo/               # video, pcap, ảnh chụp minh chứng (P3)
└── docs/               # phân công, giao diện module, quy trình git, nhật ký
```

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .                 # cài package tcpfc ở chế độ dev
```

Yêu cầu: Python ≥ 3.10. Ghi phiên bản thực tế dùng khi chạy thí nghiệm vào `results/ENVIRONMENT.md`.

## Chạy

```bash
pytest                                           # kiểm thử
python scripts/run_once.py configs/base.yaml     # chạy 1 lần, in chỉ tiêu
python scripts/run_experiments.py                # chạy tất cả kịch bản × 5 seed -> results/raw/
python scripts/plot_results.py                   # vẽ biểu đồ -> plots/
```

## Quy trình làm việc

Đọc [docs/QUY_TRINH_GIT.md](docs/QUY_TRINH_GIT.md) trước khi commit. Tóm tắt:
không push thẳng vào `main`; mỗi việc = 1 issue + 1 nhánh `pX/ten-viec` + 1 Pull Request có ít nhất 1 người review.

## Sản phẩm nộp (theo đề)

- [ ] Báo cáo PDF 15–25 trang (`report/`)
- [ ] Mã nguồn + config + dữ liệu CSV + script vẽ (repo này)
- [ ] Video demo 3–5 phút / pcap / log (`demo/`)
- [ ] Slide bảo vệ
- [ ] Bảng phân công + nhật ký đóng góp ([docs/NHAT_KY_DONG_GOP.md](docs/NHAT_KY_DONG_GOP.md))
- [ ] Khai báo sử dụng AI ([docs/KHAI_BAO_AI.md](docs/KHAI_BAO_AI.md))
- [ ] File nén `ET4230_HK[ky]_N[so-nhom]_D09.zip` (dùng `scripts/make_submission.sh`)
