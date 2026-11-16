---
name: eshop-k6-performance
description: Use when preparing, running, reviewing, or documenting HW05 performance tests for eshop-sut with k6 and the login, product search/detail, cart, and checkout E2E workflow, including raw CSV analysis and AI misinterpretation review.
---

# EShop k6 Performance — HW05

Chuẩn hóa bảy giai đoạn dưới đây. **Chỉ số, ảnh, hostname, video, commit và kết luận phải có bằng chứng thực tế.** Tạo skill không đồng nghĩa đã hoàn thành bài tập. Mặc định MSSV `23120367`; ngày tên plan lấy ngày chạy thật theo `Asia/Ho_Chi_Minh`.

## Kích hoạt và phạm vi

Trong Antigravity IDE, mở thư mục gốc dự án rồi gọi `/eshop-k6-performance` hoặc yêu cầu đọc skill bằng đường dẫn. Workspace skill nằm ở `.agents/skills/eshop-k6-performance/` ([tài liệu Antigravity](https://antigravity.google/docs/skills)). Prompt mẫu:

```text
Dùng eshop-k6-performance trong .agents/skills/eshop-k6-performance/SKILL.md
cho HW05, MSSV 23120367. Khám phá backend hiện tại, tạo workspace performance,
chuẩn bị CSV >=40 tài khoản độc lập và ba plan cùng flow login → search →
detail → cart → checkout. Review trước, smoke trước tải lớn. Ghi toàn bộ AI
Audit, giữ raw logs và chỉ ghi kết quả đã đo. Khi tôi yêu cầu chạy suite,
chạy tuần tự Load/Stress/Spike/Soak và nhắc tôi quay/chụp bằng chứng.
```

Nếu chỉ được yêu cầu tạo/review plan, dừng sau bước đó; không tự chạy tải hoặc đăng GitHub/YouTube. Khi đã được yêu cầu chạy, thực hiện phạm vi đó; không hỏi lại những bước đã được cho phép. Không commit/push nếu chưa được giao. Không sửa SUT để làm kết quả đẹp hơn.

Đọc [references/hw05-checklist.md](references/hw05-checklist.md) khi lập kế hoạch và trước đóng gói. Đọc [references/implementation.md](references/implementation.md) khi sửa helper hoặc backend khác revision này. Các helper dùng Python 3.10+, Node/npm và k6 có built-in dashboard (đã kiểm tra với phiên bản trong validation notes). Không cần Grafana Cloud hay Postman.

## 1. Đọc API — API Discovery

Đọc đề `docs/2026.HW05.Performance Testing_En.pdf` nếu còn có trong dự án; đối chiếu checklist, không bỏ các yêu cầu ngoài bảy giai đoạn. Quét routes/controllers/validation schema, cấu hình port, auth middleware, database và frontend/API spec để xác định payload thực sự. Không suy đoán từ tên endpoint.

Từ project root:

```bash
python3 .agents/skills/eshop-k6-performance/scripts/bootstrap.py \
  --project . --output performance --student-id 23120367 --accounts 40
cd performance
```

`bootstrap.py` tạo snapshot có source hash/line references và dừng nếu không xác minh được adapter của revision hiện tại. Output phải là thư mục trống để không ghi đè evidence. Nếu port 3000 đã dùng, chọn `--port 3100`; ghi lại port gốc và port bản test. Không đoán remote URL; remote SUT cần adapter/reset riêng đã kiểm chứng.

Revision được hỗ trợ có:

| Bước | Method/URI | Input → output |
|---|---|---|
| Login | POST `/api/login` | `{email,password}` → `token`, `user`; Bearer JWT, không cookie |
| Search | GET `/api/products?search=...` | URL-encode keyword → array có productId |
| Detail | GET `/api/products/:id` | `id,name,price`; kiểm tra body vì không tồn tại vẫn trả 200 `{}` |
| Cart | POST `/api/cart` | `{id,name,price,quantity}` → message |
| Checkout | POST `/api/checkout` | `{total_amount,shipping_address}` → `orderId` |

Ghi nhận khác biệt với đề: code `login_attempts + 2`, ngưỡng `>=3`, khóa `180000 ms` ⇒ có thể khóa sau hai lần sai, không phải ba. Chỉ gọi đây là lỗi đã tái hiện khi thực sự chạy reproduction riêng. Giá sản phẩm ID chẵn có thể là chuỗi. Không có schema validation riêng cho flow này. Giỏ nằm trong RAM; checkout không xóa giỏ; không có cột tồn kho.

## 2. Chuẩn bị CSV và reset

```bash
python3 scripts/perf.py install
./scripts/reset_db.sh
```

Install tải npm dependencies từ lockfile và `benc-uk/k6-reporter` **3.0.4**, lưu SHA256/license; không dùng nhánh `main` trôi nổi. Reset chạy **bản backend cô lập** trong `.runtime/backend`, xóa/seed DB bản sao, xóa giỏ RAM qua restart, tạo rồi kiểm tra >=40 user fixture trong SQLite. Dữ liệu gốc `backend/database.sqlite` không bị sửa. Chỉ port/bind loopback được thay trong bản copy, có manifest ghi khác biệt.

Không chạy `npm run seed`/restart backend gốc: `require('./database')` hiện xóa/reseed mọi bảng. Helper chỉ signal PID do chính workspace quản lý và dừng khi port bận. Không reset trong lúc đo tải.

Output `data/e2e_test_data.csv` có đúng header:

```csv
email,password,keyword,productId,quantity,shippingAddress
```

Các dòng thật lấy sản phẩm từ DB seed đã chạy và tài khoản fixture được seed bổ sung, không giả định seed gốc có 40 user (seed gốc chỉ có 2). Địa chỉ chứa dấu phẩy được quote chuẩn CSV. `SharedArray` parse CSV trong init; `rows[__VU-1]` cấp một tài khoản/VU, **không modulo**. Dừng nếu số tài khoản nhỏ hơn peak VU; muốn peak cao hơn, bootstrap workspace mới với `--accounts N`. Chỉ hỗ trợ một tiến trình k6 local; distributed runners cần phân vùng tài khoản riêng.

Tồn kho: revision này **N/A**, không được bịa cột stock hay chạy SQL phỏng đoán. Khi revision có tồn kho, cập nhật adapter để snapshot/restore đúng schema trước chạy tiếp.

## 3. Ba test plan, cùng flow và ba report view

Bootstrap tạo:

```text
scripts/23120367_Load_<YYYYMMDD>.js
scripts/23120367_Stress_<YYYYMMDD>.js
scripts/23120367_Spike_<YYYYMMDD>.js
scripts/23120367_Soak_<YYYYMMDD>.js
```

Ba plan bắt buộc cùng gọi `scripts/lib/workflow.js`, có năm `group()` đúng thứ tự. Login token được truyền sang bước sau; product ID và price được kiểm tra; checkout dùng dữ liệu detail và shippingAddress CSV. Mọi response kiểm tra HTTP 200/201 và body; thất bại dừng flow hiện tại, không retry login sai. Ghi duration từng bước, flow duration/outcome, phase recovery và HTTP status.

| Plan | Profile mặc định (cần review và hiệu chỉnh) | Report riêng |
|---|---|---|
| Load | 0→10 VU/30s; giữ 2m; giảm 30s | Built-in Web Dashboard `reports/load/load_dashboard.html` |
| Stress | 10→20→40, giữ peak, giảm; tổng 4m | `handleSummary` + k6-reporter classic tabbed HTML `reports/stress/stress_summary.html` |
| Spike | 10→40 trong 1s, giữ 1m, giảm 1s, recovery 1m | Custom `handleSummary` HTML group breakdown + mọi status tại `reports/spike/spike_breakdown.html` |
| Soak | 10 VU liên tục 600s (chọn 600–900s) | `reports/soak/soak_dashboard.html`, bổ sung ngoài ba view |

Think-time mặc định 1s giữa các bước và cuối vòng; smoke không có delay. Các env `LOAD_VUS`, `PEAK_VUS`, `SOAK_VUS`, `SOAK_SECONDS`, `THINK_SECONDS`, `P95_MS`, `ERROR_RATE` điều chỉnh cấu hình. p95 1500ms/error 1% chỉ là budget khởi đầu để review, **không phải kết luận đạt/ngưỡng phần cứng**. Closed VU model phù hợp phiên mua hàng; stress chưa suy giảm ở 40 VU thì chỉ xác minh được mức này, phải thử mức cao hơn với đủ accounts nếu cần tìm trần.

Lưu output AI gốc và bảng human review: sai gì, sửa gì, vì sao AI bỏ sót. Không tạo giả lỗi AI. Giữ nguyên naming convention bài tập thay vì kebab-case mặc định của skill k6 khác.

## 4. Smoke trước tải lớn

```bash
./scripts/run.sh Load --smoke
./scripts/run.sh Stress --smoke
./scripts/run.sh Spike --smoke
```

Mỗi lệnh chạy đúng **1 VU, 1 iteration**, vô hiệu profile tải lớn bằng `SMOKE=1`, dùng output `Smoke_*` riêng. CSV, token, năm HTTP/business checks và ít nhất một checkout phải đạt. k6 inspect chỉ kiểm tra cấu hình, không thay smoke thực thi. Không dùng smoke làm bằng chứng full scenario; dashboard smoke có thể không có chart vì quá ngắn.

Nếu smoke lỗi, điều tra dữ liệu/API/auth và sửa; đừng tiếp tục tải lớn hoặc xóa failed logs. Để smoke lại, lưu workspace mới/archive nguyên workspace; helper không ghi đè kết quả. Reset trước lần đo full để dữ liệu bắt đầu đồng nhất.

## 5. Chạy tuần tự và lưu bằng chứng

Sau review, chọn **một** cách chạy:

```bash
# Suite: reset → smoke Load → reset từng scenario → Load/Stress/Spike/Soak.
./scripts/run.sh all --pause-for-evidence

# Hoặc chạy thủ công trong workspace chưa có các output cùng tên:
./scripts/reset_db.sh
./scripts/run.sh Load --pause-for-evidence
./scripts/reset_db.sh
./scripts/run.sh Stress --pause-for-evidence
./scripts/run.sh Spike --pause-for-evidence
SOAK_VUS=10 SOAK_SECONDS=600 ./scripts/run.sh Soak --pause-for-evidence
```

Nếu đã smoke riêng, dùng cách thủ công hoặc workspace mới; `all` không ghi đè smoke có sẵn. Runner tự reset sau Stress/Spike (và trước mỗi scenario trong suite); nếu đã thao tác API sau reset tự động, chạy lại reset trước Soak. Mỗi lần chạy xuất raw CSV, summary JSON, command/version/hash/exit manifest và backend CPU/RSS CSV:

```bash
# Dạng lệnh k6 do runner thực hiện, từ workspace:
K6_WEB_DASHBOARD=true K6_WEB_DASHBOARD_PORT=-1 \
K6_WEB_DASHBOARD_EXPORT=reports/load/load_dashboard.html \
BASE_URL=http://127.0.0.1:3000 SCENARIO_TYPE=Load \
k6 run --out csv=raw_logs/23120367_Load_raw.csv \
  --summary-export=raw_logs/Load_summary.json scripts/23120367_Load_<YYYYMMDD>.js
# Stress/Spike: dashboard=false; runner chọn handleSummary/report path tương ứng.
```

Runner phát nhắc trước/sau từng run: Terminal + Activity Monitor **cùng khung hình**, chọn backend PID thật, ảnh DURING-run, giọng tiếng Việt của sinh viên, commit riêng từng bước. `--pause-for-evidence` cho thời gian bố trí quay. Không tự giả mạo/đánh dấu hoàn thành ảnh/video. Hostname dự kiến từ user là `Thuys-MacBook-Air`; thu hostname thật và xác minh khớp bài trước, không ghi đè hostname máy.

```bash
./scripts/collect_hardware.sh
# Chụp thủ công: evidence/hardware.png, Load_screen.png, Stress_screen.png,
# Spike_screen.png, Soak_screen.png. Điền bảng CPU/RAM/OS/model/hostname.
git log --date=iso-strict --pretty=fuller --stat > evidence/git-log.txt
```

Exit 99 là **threshold breach**, giữ và phân tích, không gọi là pass; lỗi tool khác cần xử lý trước tiếp tục. Soak giữ tải 10–15 phút, không reset giữa lúc đo; xác định ổn định theo p95/error/RSS, báo RPS và RAM bằng số. Muốn gọi tối đa, có bằng chứng vùng ổn định và vùng suy giảm; nếu chưa có, ghi “highest verified sustained load”, không suy diễn trần từ một run. Carts không được xóa có thể gây memory growth: ghi nhận đặc tính/issue thay vì âm thầm sửa SUT.

## 6. Phân tích raw CSV

Runner tự gọi analyzer; có thể chạy lại phép tính (raw CSV giữ nguyên):

```bash
python3 scripts/analyze_raw.py raw_logs/23120367_Load_raw.csv --output-prefix analysis/Load
python3 scripts/analyze_raw.py raw_logs/23120367_Stress_raw.csv --output-prefix analysis/Stress
python3 scripts/analyze_raw.py raw_logs/23120367_Spike_raw.csv --output-prefix analysis/Spike
python3 scripts/analyze_raw.py raw_logs/23120367_Soak_raw.csv --output-prefix analysis/Soak
python3 scripts/analyze_resources.py evidence/Soak_resources.csv
# Ví dụ plateau Load sau ramp-up; window phải nằm trong thời gian chạy thật:
python3 scripts/analyze_raw.py raw_logs/23120367_Load_raw.csv \
  --from-seconds 30 --to-seconds 150 --output-prefix analysis/Load_plateau
# Spike: recovery sau giây92; Soak600s: có thể đối chiếu các window60s.
```

Analyzer tạo JSON+Markdown min/avg/med/p90/p95/p99/max theo endpoint và HTTP overall; flow latency có metric riêng. Percentile Type-7 từ mẫu gốc, không trung bình percentile. Latency ms; error_rate dạng 0..1. `run_start_ms`/`run_end_ms` cung cấp cửa sổ setup→teardown chung; RPS = tổng http_reqs / giây cửa sổ, checkout/s = flow_completed / cùng cửa sổ. Không dùng khoảng cách giữa hai sample endpoint làm denominator. Chỉ dùng `--duration-seconds` với log ngoài helper khi đã có nguồn thời lượng xác minh được.

HTTP error rate lấy `http_req_failed` theo expectedStatuses 200/201, có network failure; flow error rate lấy business outcomes; attempts bị ngắt được ghi riêng. Thiếu metric/count không khớp/không có cửa sổ thì dừng. **summary JSON không thể khôi phục raw samples**; yêu cầu chạy lại/đánh dấu thiếu bằng chứng. Không đổi tên CSV thành `.jtl`: đề cho k6 nhưng ghi literal JMeter `.jtl`, cần ghi chỗ chưa thống nhất và xác nhận TA chấp nhận native k6 CSV.

## 7. Kiểm chứng AI và hoàn thiện bài

Copy template có sẵn (không phải báo cáo hoàn chỉnh):

```bash
cp templates/ai-verification.md analysis/ai-verification.md
cp templates/main-report.md reports/main-report.md
cp templates/continuous-performance.md reports/continuous-performance.md
cp templates/README.md README.md
cp templates/links.json evidence/links.json
```

Đưa raw logs/analysis đã tính cho AI, lưu nguyên phân tích đầu tiên và đề xuất threshold, rồi **sinh viên** đối chiếu vào bảng bốn cột chính xác:

`Chỉ số / Nhận định của AI | Giá trị trích xuất từ Raw CSV Log | Đánh giá (Chính xác / Sai lệch / Ảo giác) | Giải thích nguyên nhân kỹ thuật`

Ghi raw filename/hash, metric, số mẫu, cửa sổ, giá trị đúng và lý do sai. Phân loại đề xuất tối ưu khả thi/hallucinated/chưa xác minh bằng code/schema/query-plan hoặc thí nghiệm: SQLite WAL không tự động là lời giải; không áp advice PostgreSQL pool vào một sqlite3 Database; không bịa stock; index cần xét LIKE '%keyword%'.

Ghi AI Audit **từ tương tác đầu tiên**, không đợi đến cuối:

```bash
python3 scripts/record_audit.py --tool 'Antigravity / actual model' \
  --at '2026-11-16T16:00:00+07:00' \
  --prompt /absolute/path/to/actual-prompt.md --final-output /absolute/path/to/final-response.md
```

Thay timestamp ví dụ bằng thời điểm tương tác thật. Mỗi lượt hỏi–đáp ghi tool/model, ngày giờ, prompt và **câu trả lời cuối cùng hiển thị cho người dùng của lượt đó** vào một file `audit/ai-audit.md`; xuất PDF khi nộp. Không ghi suy nghĩ nội bộ, reasoning, commentary/progress, tool-call traces hay log terminal trung gian vào AI Audit. Không gộp cả bài thành duy nhất câu trả lời cuối: giữ final response của từng tương tác, đặc biệt phân tích AI đầu tiên dùng cho Task 2. Raw logs test vẫn lưu riêng đầy đủ.

Helper chỉ append Markdown, không tạo `interactions/` hoặc `interactions.jsonl`, không tự đọc/lọc chat history. Agent chọn đúng final response trước khi gọi helper; không đưa toàn bộ transcript vào `--final-output`. Alias `--output` được giữ để tương thích lệnh cũ. Có thể điền Markdown trực tiếp theo cùng cấu trúc. Nếu đã có bản lưu cũ, chỉ bỏ các bản trùng sau khi kiểm tra prompt/final response đã nằm đầy đủ trong Markdown và các link không còn trỏ vào chúng. Không bịa tương tác còn thiếu hoặc ghi đè human review. AI Audit phải khai báo sử dụng AI; review do sinh viên viết. AI Critique riêng **một đoạn 200–300 từ**, nêu sai/thiếu/thiên lệch, nguyên nhân, bài học; AI không viết thay để giả là đánh giá người học.

Task 3 trong kết luận: theo dõi commit → quyết định test → p95 regression gate; có flowchart, baseline, chi phí/false alarms. Template có Mermaid, chưa phải pipeline đã triển khai. Báo issue thật kèm ảnh lên GitHub khi được giao đăng; nếu chưa có quyền thì tạo nội dung reviewable, không tự gửi. Video unlisted >=6 phút tổng, có demo dùng skill end-to-end trên nhóm endpoint đầy đủ. Skill này và nguồn tham khảo phải có trong bài nộp.

Xuất main report, Audit, Critique thành **Markdown+PDF**, render và kiểm tra PDF. Điền README tự chấm 30/20/20/10/10/10, số liệu soak, số issue, public repo và video. Dùng checker:

```bash
python3 scripts/check_submission.py
python3 scripts/perf.py stop
```

Checker phát hiện thiếu file/cấu trúc; không chứng thực giọng nói, ảnh hay human review. Đọc checklist thủ công trước ZIP `<StudentID>_HW05_AI_Performance_<000..100>.zip`. Không tự cho điểm, tự tạo PDF kết quả rỗng, publish hay nộp Moodle. Hạn xem Moodle; thiếu tài liệu bắt buộc có thể 0 điểm. Commit theo từng bước khi user giao commit, giữ git-log text; chuẩn bị giải thích trong vấn đáp.
