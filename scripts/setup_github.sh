#!/usr/bin/env bash
# Tạo label, milestone và các issue ban đầu trên GitHub (P1 chạy 1 lần sau khi push repo).
# Yêu cầu: GitHub CLI đã đăng nhập (gh auth login), chạy trong thư mục repo.
# Dùng: bash scripts/setup_github.sh
set -euo pipefail
URL=$(git remote get-url origin); URL=${URL%.git}; REPO=${REPO:-${URL#*github.com/}}
echo "Repo: $REPO"

label(){ gh api "repos/$REPO/labels" -f name="$1" -f color="$2" >/dev/null 2>&1 || true; }
for p in P1 P2 P3 P4; do label "$p" 1d76db; done
label task 0e8a16; label report fbca04

declare -a MS=("T1 - De xuat & giao dien" "T2 - Ban chay toi thieu" "T3 - Du chuc nang"
               "T4 - Thi nghiem" "T5 - Phan tich & bao cao" "T6 - Hoan thien & nop")
for m in "${MS[@]}"; do
  gh api "repos/$REPO/milestones" -f title="$m" >/dev/null 2>&1 || true
done

ms_num(){ gh api "repos/$REPO/milestones?state=all&per_page=100" --jq ".[] | select(.title==\"$1\") | .number"; }
issue(){ # $1=label $2=milestone $3=title $4=body   (dùng REST API)
  local n; n=$(ms_num "$2")
  gh api "repos/$REPO/issues" -f title="$3" -f body="$4" -f "labels[]=$1" -f "labels[]=task" -F milestone="$n" >/dev/null && echo "  + $3"; }

M1="${MS[0]}"; M2="${MS[1]}"; M3="${MS[2]}"; M4="${MS[3]}"; M5="${MS[4]}"; M6="${MS[5]}"

issue P4 "$M1" "[P4] Gửi đề xuất + bảng phân công cho giảng viên" "Mục tiêu, sơ đồ mô hình, công cụ, giả định, baseline, phân công (lưu ý nhóm 4 người: 3 code + 1 báo cáo)."
issue P1 "$M1" "[Nhóm] Chốt docs/GIAO_DIEN.md và segment.py" "Cả 4 người review & approve PR."
issue P4 "$M1" "[P4] Dựng khung báo cáo, thống nhất định dạng (Markdown→PDF hay Word/LaTeX)" ""
issue P3 "$M2" "[P3] Hiện thực channel.py (trễ RTT/2, mất gói Bernoulli, seed)" "Bỏ @pytest.mark.todo trong tests/test_channel.py khi xong."
issue P1 "$M2" "[P1] Sender: sliding window + xử lý ACK" "test_never_exceeds_rwnd, test_ack_slides_window."
issue P2 "$M2" "[P2] Receiver: buffer, rcv_nxt, rwnd trong ACK" "test_rwnd_decreases_as_buffer_fills, test_zero_window_when_full..."
issue P2 "$M2" "[P2] Metrics: hàm ghi + time_weighted_mean + summary()" "tests/test_metrics.py."
issue P1 "$M2" "[P1] simulation.run() end-to-end không mất gói" "test_all_bytes_delivered_no_loss, test_window_limited_goodput_close_to_theory."
issue P4 "$M2" "[P4] Viết báo cáo mục 1, 2, 10 (mục tiêu, lý thuyết, tài liệu tham khảo)" "RFC 9293, RFC 6298, RFC 1122; phân biệt flow control vs congestion control."
issue P1 "$M3" "[P1] Sender: RTO + Go-Back-N, persist timer + window probe" "test_zero_window_stops_and_probes, test_timeout_retransmits_from_snd_una."
issue P2 "$M3" "[P2] Receiver: app read định kỳ + window update + out-of-order" "test_window_update_after_app_read, test_out_of_order_then_fill_gap."
issue P3 "$M3" "[P3] Demo TCP thật: slow_server/fast_client trên 2 máy + Wireshark" "Chụp ZeroWindow / ZeroWindowProbe / Window Update, lưu pcap."
issue P3 "$M3" "[Nhóm P1–P3] Ghi chú kỹ thuật docs/ghi_chu/pX.md bản 1" "Mỗi người code viết ghi chú module của mình để P4 viết mục 3–6."
issue P4 "$M3" "[P4] Viết báo cáo mục 3, 4, 5, 6 + sơ đồ khối, sơ đồ trình tự" "Dựa trên docs/ghi_chu/p1..p3.md."
issue P3 "$M4" "[P3] run_experiments.py: 3 kịch bản × 4 tham số quét × 5 seed -> CSV" "results/raw/*.csv, results/summary.csv."
issue P3 "$M4" "[P3] plot_results.py: 5 biểu đồ tối thiểu" "Tiêu đề, đơn vị, chú giải, error bar."
issue P1 "$M4" "[P1] Thí nghiệm sweep_rtt, sweep_loss: kiểm tra & nhận xét" "Ghi nhận xét vào docs/ghi_chu/p1.md mục 6."
issue P2 "$M4" "[P2] Thí nghiệm S1–S3, sweep_buffer, sweep_app_rate: receiver bottleneck" "So sánh lý thuyết min(B/RTT, R_app); ghi nhận xét vào docs/ghi_chu/p2.md mục 6."
issue P4 "$M4" "[P4] Viết báo cáo mục 7, 8 (kết quả, phân tích, đối chiếu TCP thật)" "Tách Quan sát – Nhận định – Giới hạn."
issue P3 "$M5" "[P3] Quay video demo 3–5 phút" ""
issue P4 "$M5" "[P4] Viết mục 9, ghép báo cáo PDF, làm slide bảo vệ" "P1–P3 mỗi người góp 2–4 slide nội dung."
issue P4 "$M6" "[P4] Nhật ký đóng góp, khai báo AI, rà checklist mục VII" ""
issue P1 "$M6" "[Nhóm] Chạy lại toàn bộ trên máy sạch, nén & nộp" "bash scripts/make_submission.sh <ky> <nhom>"
echo "Xong. Nhớ bật branch protection cho main (Settings → Branches)."
