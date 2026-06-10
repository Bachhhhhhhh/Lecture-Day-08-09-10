# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

> User / agent thấy gì? (VD: trả lời “14 ngày” thay vì 7 ngày)
User / chatbot agent sẽ truy xuất thông tin lỗi thời (VD: trả lời khách hàng rằng thời gian hoàn tiền là "14 ngày" thay vì chính sách mới là "7 ngày"). Hoặc hệ thống trả về những văn bản nhiễu "Nội dung không rõ ràng: ...".

---

## Detection

> Metric nào báo? (freshness, expectation fail, eval `hits_forbidden`)
- Quá trình Data Pipeline cảnh báo/halt expectation: `refund_no_stale_14d_window` báo `FAIL`, pipeline dừng lại (nếu không skip-validate).
- Pipeline trả về Freshness status `FAIL` do `latest_exported_at` đã quá hạn 24 giờ.
- Đánh giá Evaluation `artifacts/eval/*.csv` ghi nhận `hits_forbidden = yes` cho câu hỏi truy vấn policy hoàn tiền.

---

## Freshness Check (Giải thích PASS/WARN/FAIL)

Khi chạy lệnh `python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_<run-id>.json`:
- **PASS**: Ngày xuất dữ liệu `latest_exported_at` ở mức an toàn (<= 24 giờ). Dữ liệu hoàn toàn tươi mới, an tâm sử dụng.
- **WARN**: (Nếu có cấu hình ngưỡng Warning) Dữ liệu sắp hết hạn (ví dụ > 20 giờ nhưng <= 24 giờ). Cần báo cho team Data chuẩn bị export dữ liệu mới.
- **FAIL**: Tuổi của dữ liệu `age_hours` đã vượt quá SLA (24.0 giờ). Trạng thái `freshness_sla_exceeded` sẽ xuất hiện. Lúc này, pipeline dừng cảnh báo để kỹ sư can thiệp vì dữ liệu đưa vào Vector DB đã quá cũ, dễ gây rủi ro agent trả lời sai thông tin.

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra `artifacts/manifests/*.json` | Xem có cờ `skipped_validate = true` không. Kiểm tra `latest_exported_at` để đánh giá freshness. |
| 2 | Mở `artifacts/quarantine/*.csv` | Kiểm tra nguyên nhân dữ liệu bị đẩy vào quarantine (VD: `stale_refund_window`, `noisy_prefix`). |
| 3 | Chạy `python eval_retrieval.py` | Kiểm tra kết quả `hits_forbidden = False` trên file evaluation (`after_fix_eval.csv`). Đảm bảo kết quả retrieval đã sạch. |

---

## Mitigation

> Rerun pipeline, rollback embed, tạm banner “data stale”, …
Nếu dữ liệu sai sót đã lên production (ChromaDB):
- Kiểm tra lại các rule filter trong `cleaning_rules.py` để bổ sung logic chặn từ khóa lỗi thời.
- Chạy lại pipeline bình thường `python etl_pipeline.py run` để tự động kích hoạt quá trình `embed_prune_removed` xóa đi các document cũ đã bị thay thế hoặc quarantine.
- Trong trường hợp khẩn cấp, thiết lập thông báo banner "Data is stale" ở giao diện của Chatbot hoặc gửi cảnh báo cho bộ phận CS.

---

## Prevention

> Thêm expectation, alert, owner — nối sang Day 11 nếu có guardrail.
- Thêm các expectation khắt khe (VD: độ dài tối thiểu, không chứa blacklist keyword) trong file `expectations.py` và đặt flag `halt = True`.
- Cấu hình Alert bằng cách đọc Manifest file, tự động thông báo qua kênh Slack (#data-alerts) khi `PIPELINE_HALT` diễn ra.
- Chỉ định Data Owner để làm rõ ai là người chịu trách nhiệm cung cấp CSV chuẩn ở `data_contract.yaml`.
