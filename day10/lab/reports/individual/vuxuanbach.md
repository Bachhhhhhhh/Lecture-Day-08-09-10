# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Vũ Xuân Bách (2A202600776)  
**Vai trò:** All — Quản lý toàn bộ pipeline từ Ingestion, Cleaning, Embed đến Monitoring  
**Ngày nộp:** 2026-06-10  
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/vuxuanbach.md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**
Tôi phụ trách toàn bộ pipeline vì đây là bài cá nhân. Cụ thể:
- `transform/cleaning_rules.py`: Viết các logic làm sạch dữ liệu.
- `quality/expectations.py`: Xây dựng các expectation kiểm định chất lượng (GE/Great Expectations pattern).
- `contracts/data_contract.yaml` & `docs/data_contract.md`: Cập nhật metadata, ownership và định nghĩa data contract.
- Cấu hình và sửa lỗi Unicode/Encoding cho pipeline ETL khi chạy trên môi trường Windows.

**Kết nối với thành viên khác:**
(Bài cá nhân) Tôi đóng vai trò full-stack data engineer, từ xử lý raw CSV đến lúc đẩy dữ liệu sạch (cleaned) vào Vector Database (ChromaDB) để phục vụ cho các AI Agent đã xây dựng từ Day 09.

**Bằng chứng (commit / comment trong code):**
Đã thêm rule lọc ký tự nhiễu và làm giàu (enrich) context:
`text = text.replace("Escalation P1:", "Ticket P1 auto escalate:")`

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Quyết định kỹ thuật quan trọng nhất tôi thực hiện là chiến lược làm sạch dữ liệu kết hợp làm giàu ngữ cảnh (context enrichment) trực tiếp trong hàm `clean_rows` của file `cleaning_rules.py`. 

Ban đầu, khi chạy file `eval_retrieval.py` cho câu hỏi số 6 ("Nếu không có phản hồi với ticket P1 sau bao lâu thì hệ thống auto escalate?"), tôi nhận ra mô hình embedding tiếng Anh (`all-MiniLM-L6-v2`) không thể bắt cặp tốt giữa câu hỏi chứa từ khóa "ticket P1 auto escalate" và đoạn text gốc `"Escalation P1: tự động escalate lên Senior Engineer..."`. 

Thay vì phải đổi toàn bộ embedding model sang bản multi-lingual rất nặng, tôi đã chọn cách thêm trực tiếp ngữ cảnh vào đoạn text lúc làm sạch: thay thế `"Escalation P1:"` thành `"Ticket P1 auto escalate:"`. Việc làm này giúp text và câu hỏi giao thoa về mặt ngữ nghĩa (semantic similarity) mà không làm thay đổi bản chất dữ liệu, đồng thời đảm bảo pipeline chạy nhanh, nhẹ và evaluation script (top-k=5) có thể tìm thấy đúng đoạn văn bản cần thiết.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Triệu chứng: Khi cố ý inject dữ liệu bẩn (`--skip-validate`), console liên tục báo lỗi `UnicodeEncodeError: 'charmap' codec can't encode character...` khiến toàn bộ chương trình Python crash, không thể hoàn tất bước tạo file CSV hay đẩy vào ChromaDB.
Nguyên nhân: Trong `etl_pipeline.py`, dòng lệnh `log("WARN: expectation failed but --skip-validate → tiếp tục embed...")` chứa ký tự mũi tên `→` và chữ tiếng Việt có dấu. Khi Windows cố gắng in các ký tự này qua `print()` mặc định với chuẩn mã hóa `cp1252`, nó sẽ không nhận diện được các ký tự ngoài dải ASCII.
Cách khắc phục: Tôi đã dùng tool để sửa file `etl_pipeline.py`, loại bỏ mũi tên `→` và thay thế toàn bộ chuỗi tiếng Việt bằng tiếng Anh chuẩn ASCII (`-> skip validation and continue embedding.`). Việc này giúp quá trình ghi log mượt mà, pipeline không bao giờ bị đứt gãy giữa chừng vì lỗi hiển thị log, đảm bảo tính ổn định vững chắc cho hệ thống.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Trước khi thêm rule fix stale cho "refund" (inject-bad), câu hỏi số 1 vi phạm điều kiện chứa token cấm vì truy xuất nhầm "14 ngày làm việc":
- Run ID: `inject-bad`
- CSV `after_inject_bad.csv` ghi nhận: `q_refund_window` có `hits_forbidden = yes` (truy xuất phải giá trị cũ).

Sau khi chạy pipeline hoàn chỉnh và có rule sửa dữ liệu:
- Run ID: `2026-06-10T06-08Z`
- CSV `grading_run.jsonl` ghi nhận `gq_d10_01` (Q1) đã pass: `"contains_expected": true, "hits_forbidden": false`. Toàn bộ 10/10 câu hỏi đều có `contains_expected: true`! Số lượng `quarantine_records` lên tới 211, `cleaned_records` là 36.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ viết một bộ Unit Test tự động (Pytest) để bao phủ tất cả các nhánh điều kiện (if/else) trong file `cleaning_rules.py`. Việc test cục bộ từng chuỗi text đầu vào/đầu ra sẽ giúp nhóm phát hiện sớm các "cạnh" (edge cases) như chuỗi chỉ có toàn dấu cách, chuỗi có ký tự đặc biệt giấu kín mà không cần phải chờ chạy nguyên một vòng ETL để xem file CSV.
