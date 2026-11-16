# Báo cáo (15–25 trang, không tính phụ lục)

**P4 viết toàn bộ** các section bằng Markdown trong `sections/`, dựa trên ghi chú kỹ thuật `docs/ghi_chu/p1..p3.md`, CSV trong `results/` và hình trong `plots/`. Xuất PDF, ví dụ:
```bash
pandoc report/sections/*.md -o report/ET4230_D09_BaoCao.pdf --pdf-engine=xelatex -V mainfont="Times New Roman" --toc
```
(hoặc chuyển sang Word/LaTeX nếu nhóm thích – thống nhất ở tuần 4).
Hình lấy từ `plots/`, luôn ghi: tham số, số seed, đơn vị.

| File | Nội dung | Nguồn tư liệu cho P4 | Trang (dự kiến) |
|---|---|---|---|
| 01_muc_tieu.md | Mục tiêu, phạm vi, phân biệt flow vs congestion control | đề bài, P4 tự viết | 1–2 |
| 02_ly_thuyet.md | Sliding window, seq/ACK, advertised window, zero window, persist timer, SWS; tài liệu | P4 tự nghiên cứu | 3–4 |
| 03_kien_truc_mo_phong.md | Kiến trúc, engine sự kiện, mô hình kênh, giả định | ghi_chu/p3.md | 2–3 |
| 04_mo_hinh_ben_gui.md | Thuật toán bên gửi, RTO, probe | ghi_chu/p1.md | 2 |
| 05_mo_hinh_ben_nhan.md | Bộ đệm, rwnd, ứng dụng đọc, window update | ghi_chu/p2.md | 2 |
| 06_thiet_ke_thi_nghiem.md | Kịch bản, tham số cố định/biến đổi, chỉ tiêu & công thức, seed | ghi_chu/p2.md, configs/ | 2 |
| 07_phan_tich.md | Kết quả, biểu đồ, so sánh lý thuyết, receiver bottleneck | plots/, results/, ghi_chu/p1–p3 | 4–6 |
| 08_doi_chieu_tcp_that.md | Thí nghiệm TCP thật + Wireshark, so sánh định tính | ghi_chu/p3.md, demo/ | 2 |
| 09_han_che_ket_luan.md | Hạn chế, bài học, kết luận | mục 7 của mọi ghi chú | 1–2 |
| 10_tai_lieu_tham_khao.md | RFC 9293, RFC 6298, RFC 1122 (SWS), giáo trình… | P4 | 1 |
| 11_phu_luc.md | Phân công, nhật ký, khai báo AI, hướng dẫn chạy | docs/, README | – |
