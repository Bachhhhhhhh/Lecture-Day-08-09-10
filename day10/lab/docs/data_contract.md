# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `policy_refund_v4` | Export CSV định kỳ | Chunk lỗi thời (14 ngày thay vì 7 ngày) | Cảnh báo expectation khi tồn tại rule cũ |
| `hr_leave_policy` | API Sync | Dữ liệu cũ bị dính vào do conflict version | Alert nếu ngày hiệu lực trước 2026 hoặc có text cũ |
| `it_helpdesk_faq` | Database dump | Noise text (Nội dung không rõ ràng) | Alert nếu parse chunk có tiền tố nhiễu |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | … |
| doc_id | string | Có | … |
| chunk_text | string | Có | … |
| effective_date | date | Có | … |
| exported_at | datetime | Có | … |

---

## 3. Quy tắc quarantine vs drop

Những record không thoả mãn điều kiện làm sạch (Clean) sẽ được gán cờ (`flag`) và chuyển vào file cách ly (quarantine).
- **Quarantine**: Được lưu thành file CSV `artifacts/quarantine/quarantine_<run-id>.csv` thay vì bị xóa vĩnh viễn. Việc này phục vụ cho truy vết lỗi hệ thống.
- **Merge lại**: Data Engineer hoặc Data Owner sẽ phân tích file quarantine. Nếu phát hiện bị chặn nhầm, họ sẽ cập nhật file `cleaning_rules.py` hoặc `expectations.py` rồi chạy lại pipeline.

---

## 4. Phiên bản & canonical

Source of truth (nguồn chính thống) cho các document:
- **Refund Policy**: Chỉ chấp nhận bản `policy_refund_v4` với cửa sổ hoàn tiền là 7 ngày.
- **HR Leave Policy**: Chỉ lấy nội dung có `effective_date` từ năm 2026 trở đi (phiên bản 12 ngày phép năm). Phiên bản 2025 (10 ngày) sẽ bị reject.
- Nguồn Canonical cuối cùng được định nghĩa rõ ràng tại `contracts/data_contract.yaml`.
