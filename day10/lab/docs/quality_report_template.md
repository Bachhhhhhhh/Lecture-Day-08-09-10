# Quality report — Lab Day 10 (nhóm)

**run_id:** _______________  
**Ngày:** _______________

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước | Sau | Ghi chú |
|--------|-------|-----|---------|
| raw_records | 247 | 247 | Dữ liệu gốc giống nhau |
| cleaned_records | 45 | 36 | Pipeline sau khi chạy `inject-bad` dính phải 9 record lỗi thời. Sau fix, số cleaned_records giảm còn 36 |
| quarantine_records | 202 | 211 | Nhờ rule chặn data cũ, 9 record này bị đẩy vào khu vực cách ly, đưa tổng số bị cách ly lên 211 |
| Expectation halt? | Halt | Halt | Nếu không pass cờ `--skip-validate` |

---

## 2. Before / after retrieval (bắt buộc)

> Đính kèm hoặc dẫn link tới `artifacts/eval/before_after_eval.csv` (hoặc 2 file before/after).

**Câu hỏi then chốt:** refund window (`q_refund_window`)  
**Trước:** `Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn.` (hits_forbidden = yes)
**Sau:** `Yêu cầu được gửi trong vòng 7 ngày làm việc làm việc kể từ thời điểm xác nhận đơn hàng.` (hits_forbidden = no)

**Merit (khuyến nghị):** versioning HR — `q_leave_version` (`contains_expected`, `hits_forbidden`, cột `top1_doc_expected`)

*(Phần HR Policy đã được bảo vệ bởi rule lọc ngày hiệu lực `effective_date >= 2026` ngay từ baseline, do đó kể cả khi inject-bad (bỏ qua rule refund), dữ liệu HR vẫn sạch và đạt `contains_expected = true`.)*

---

## 3. Freshness & monitor

> Kết quả `freshness_check` (PASS/WARN/FAIL) và giải thích SLA bạn chọn.
Kết quả cho file manifest báo cáo là `FAIL` và `freshness_sla_exceeded`. Điều này là chính xác vì dữ liệu trong file CSV (export mock) là ngày `2026-04-10`, khi so sánh với hiện tại, thời gian đã trôi qua trên 24 giờ. Cấu hình SLA 24 giờ là hợp lý để nhắc Data Team cung cấp bản dump mới nhất.

---

## 4. Corruption inject (Sprint 3)

> Mô tả cố ý làm hỏng dữ liệu kiểu gì (duplicate / stale / sai format) và cách phát hiện.
Sử dụng cờ `--no-refund-fix --skip-validate` để cố tình bypass việc xóa document cũ (14 ngày). Hệ thống được phát hiện thông qua việc expectation `refund_no_stale_14d_window` báo lỗi, nhưng do skip validate nên nó vẫn lọt xuống Embedding DB. Hậu quả là eval `hits_forbidden` trở thành Yes.

---

## 5. Hạn chế & việc chưa làm

- Thiếu việc tích hợp Cronjob tự chạy Pipeline để đảm bảo độ tươi mới của DB.
- Bộ từ khóa chặn (Stopwords/Blacklist) vẫn đang code cứng (hard-code) trong `cleaning_rules.py`. Việc này có thể mở rộng bằng cách dùng 1 file dictionary bên ngoài.
