# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** ___________  
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Học viên | All | hocvien@example.com |

**Ngày nộp:** ___________  
**Repo:** ___________  
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Nộp tại:** `reports/group_report.md`  
> **Deadline commit:** xem `SCORING.md` (code/trace sớm; report có thể muộn hơn nếu được phép).  
> Phải có **run_id**, **đường dẫn artifact**, và **bằng chứng before/after** (CSV eval hoặc screenshot).

---

## 1. Pipeline tổng quan (150–200 từ)

> Nguồn raw là gì (CSV mẫu / export thật)? Chuỗi lệnh chạy end-to-end? `run_id` lấy ở đâu trong log?

**Tóm tắt luồng:**

Pipeline nhận dữ liệu từ các hệ thống bằng file CSV xuất thô `policy_export_dirty.csv`. Dữ liệu sẽ đi qua quy trình extract, sau đó vào bước clean_rows để chuẩn hóa ngày tháng, loại bỏ bản ghi không thuộc allowlist, xóa text trùng lặp và loại bỏ các dữ liệu rác/cũ theo rules được khai báo. Tiếp đến expectation suite kiểm tra chất lượng chặt chẽ để đảm bảo không bị "halt". Cuối cùng là embed các chunk hợp lệ vào vector store (ChromaDB) thông qua cơ chế upsert dựa trên `chunk_id`.

**Lệnh chạy một dòng (copy từ README thực tế của nhóm):**

`python etl_pipeline.py run && python grading_run.py --out artifacts/eval/grading_run.jsonl`

---

## 2. Cleaning & expectation (150–200 từ)

> Baseline đã có nhiều rule (allowlist, ngày ISO, HR stale, refund, dedupe…). Nhóm thêm **≥3 rule mới** + **≥2 expectation mới**. Khai báo expectation nào **halt**.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

| Rule / Expectation mới (tên ngắn) | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| Rule: Lọc độ dài < 8 ký tự | Cảnh báo expectation chunk_min_length_8 | 0 violations cảnh báo | Log `etl_pipeline.py` |
| Rule: Dữ liệu HR stale "10 ngày phép năm" | Lỗi (Halt) expectation hr_leave_no_stale_10d_annual | Pass expectation, 0 violations | Log `etl_pipeline.py` |
| Rule: Xóa các tiền tố nhiễu | Lỗi (Halt) expectation no_noisy_prefixes | Pass expectation, 0 violations | Log `etl_pipeline.py` |

**Rule chính (baseline + mở rộng):**

- Allowlist: Mở khóa thêm tài liệu `access_control_sop` để đáp ứng câu hỏi eval.
- Stale HR Policy: Quarantine các policy có đoạn text "10 ngày phép năm" hoặc ngày < 2026.
- Short chunk: Ngăn các chunk không có đủ context (< 8 ký tự).
- Noise prefix: Tự động filter và strip "Nội dung không rõ ràng: " và "!!!" để text sạch.

**Ví dụ 1 lần expectation fail (nếu có) và cách xử lý:**

Khi chạy ban đầu, expectation `min_one_access_control` báo lỗi thiếu file. Cách xử lý: mở rộng `ALLOWED_DOC_IDS` trong `transform/cleaning_rules.py` để bao gồm `access_control_sop`. Lần tiếp theo chạy lại expectation đã pass.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

> Bắt buộc: inject corruption (Sprint 3) — mô tả + dẫn `artifacts/eval/…` hoặc log.

**Kịch bản inject:**

Chạy `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate` để cố ý bỏ qua quá trình kiểm tra data validation và sửa window hoàn tiền. Bằng cách dùng cờ skip-validate, hệ thống sẽ đẩy thẳng dữ liệu bẩn vào trong DB.

**Kết quả định lượng (từ CSV / bảng):**

Khi có dữ liệu bẩn được inject, quá trình retrieval sẽ lấy ra text cũ với nội dung "14 ngày làm việc" thay vì "7 ngày làm việc". Kết quả file `after_inject_bad.csv` cho thấy câu hỏi số `gq_d10_01` (về hoàn tiền) bị vi phạm điều kiện vì dính vào forbidden token ("14 ngày"). Khi chạy pipeline tốt thì expectation pass và eval cho kết quả false ở `hits_forbidden`. Điều này khẳng định pipeline đã fix thành công sự cố dữ liệu "stale".

---

## 4. Freshness & monitoring (100–150 từ)

> SLA bạn chọn, ý nghĩa PASS/WARN/FAIL trên manifest mẫu.

SLA đặt ra là 24 giờ. `freshness_check.py` sẽ so sánh `latest_exported_at` thu thập được qua file manifest trong artifact so với ngày hiện tại (mô phỏng). Nếu độ chênh lệch tuổi (age) lớn hơn SLA (24 giờ), hệ thống sẽ báo cáo trạng thái là FAIL (freshness_sla_exceeded) để kích hoạt alert. Nếu age <= 24, hệ thống trả về PASS.

---

## 5. Liên hệ Day 09 (50–100 từ)

> Dữ liệu sau embed có phục vụ lại multi-agent Day 09 không? Nếu có, mô tả tích hợp; nếu không, giải thích vì sao tách collection.

Dữ liệu sau khi embed này sẽ được collection `day10_kb` phục vụ trực tiếp làm nền tảng (vector store) cho Multi-agent đã xây dựng ở Day 09. Tức là agent Day 09 sẽ truy xuất nguồn dữ liệu sạch, không còn xung đột version và chuẩn xác 100% thay vì dữ liệu bị duplicate hay stale. Doanh nghiệp cần collection có version "cleaned" độc lập để dễ dàng bảo trì pipeline.

---

## 6. Rủi ro còn lại & việc chưa làm

- …
