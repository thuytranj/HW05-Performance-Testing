# HW05 — Kiểm thử hiệu năng EShop với k6

- **MSSV:** `23120367`
- **Ngày test plan:** `20261116` *(cần cập nhật/bootstrap theo ngày chạy thực tế `YYYYMMDD`, múi giờ `Asia/Ho_Chi_Minh` khi chạy full suite)*
- **Xác nhận luồng nghiệp vụ duy nhất trong nhóm:** `[Sinh viên xác nhận luồng login → search → detail → cart → checkout không trùng với thành viên khác]`

---

## 1. Môi trường và Khám phá API (API Discovery)

- **Tài liệu tham chiếu:** [api_discovery.md](api_discovery.md), [api_discovery.json](../data/api_discovery.json), [runtime-adaptation.json](../evidence/runtime-adaptation.json).
- **Base URL / Port:** `http://127.0.0.1:3000` (port gốc `3000`).
- **Môi trường backend:** Chạy trên **backend cô lập** tại `performance/.runtime/backend/` (chỉ thay đổi bind loopback `127.0.0.1` và giữ DB riêng tại `performance/.runtime/backend/database.sqlite`, không làm thay đổi `backend/database.sqlite` gốc). Không dùng `run_servers.sh` vì script đó gọi `killall node`.
- **SHA256 mã nguồn SUT đã xác minh:**
  - `backend/server.js`: `47573ce5a6bf9a894748d2bb56cc8d1659ad7acd033fdd6db6b3e4d9473eb487`
  - `backend/database.js`: `3366420632bb9c982905b22e3969f69515e39e7a37a4f84eba56ead7e94afed8`
  - `backend/package.json`: `c2ad90d0e4a2a37319fe4d66a70563392f0e06346fb69eb7abbe7c6ff79eb1f3`
  - `backend/package-lock.json`: `ec3f3b2dbf1622f1b1121b9d5916ab0eb74d06ed8c59b16082c52c452eebd814`

### Bảng thông số phần cứng & phần mềm (thu thập khi chạy thực tế)

| Thông số | Giá trị thực tế | Ghi chú |
|---|---|---|
| Hostname | `[Thu thập bằng ./scripts/collect_hardware.sh]` | Hostname dự kiến trước đó: `Thuys-MacBook-Air` (chỉ ghi giá trị đo thật) |
| Model / CPU / RAM / OS | `[Điền từ evidence/hardware.txt]` | Đính kèm `evidence/hardware.png` |
| Node.js / k6 version | `[Điền từ data/dependencies.json]` | — |
| Backend PID | `[PID của backend cô lập lúc đo]` | — |

### Đặc tính SUT quan sát từ mã nguồn (`backend/server.js`, `backend/database.js`)

- `backend/database.js` xóa toàn bộ bảng (`DROP TABLE IF EXISTS`) và reseed mỗi lần import; vì vậy phải dùng bản sao cô lập và không restart server gốc trong lúc đo.
- Giỏ hàng (`userCarts`) lưu trong RAM tiến trình Node.js; `POST /api/checkout` không đọc và không xóa giỏ hàng sau khi đặt đơn; bảng `products` không có cột tồn kho (stock: N/A).
- `GET /api/products/:id` trả về **HTTP 200 `{}`** khi không tìm thấy sản phẩm, và ép `price` sang kiểu `string` nếu `id` là số chẵn (`row.id % 2 === 0`).
- `GET /api/products?search=...` ghép chuỗi SQL trực tiếp (`LIKE '%${searchQuery}%'`).
- **Cơ chế khóa đăng nhập (Lockout):** Đề bài kỳ vọng khóa sau 3 lần sai, nhưng source code thực tế cộng `login_attempts + 2` và khóa khi `>= 3` trong `180000 ms` (`backend/server.js:54-58`) — tức có thể khóa sau **2 lần sai liên tiếp** (phân biệt hành vi đọc từ source với kết quả tái hiện thực tế nếu có reproduction riêng).

---

## 2. Thiết kế kịch bản kiểm thử và Human Review

### Luồng nghiệp vụ dùng chung (E2E Workflow)

Tất cả các kịch bản (`Load`, `Stress`, `Spike`, `Soak`) dùng chung `scripts/lib/workflow.js` gồm 5 `group()` theo đúng thứ tự, bao phủ 3 nhóm endpoint:

1. `01_auth_login` (`POST /api/login`) — **Auth-heavy**: lấy Bearer JWT (`token`) và truyền cho các bước sau.
2. `02_read_search` (`GET /api/products?search=<keyword>`) — **Read-heavy**: tìm kiếm theo từ khóa từ CSV.
3. `03_read_detail` (`GET /api/products/:id`) — **Read-heavy**: lấy chi tiết sản phẩm, kiểm tra `id`, `name`, `price` (ép kiểu số cho ID chẵn).
4. `04_transaction_cart` (`POST /api/cart`) — **Transactional**: thêm sản phẩm vào giỏ theo dữ liệu detail.
5. `05_transaction_checkout` (`POST /api/checkout`) — **Transactional**: tạo đơn với `total_amount = Number(product.price) * quantity` và `shippingAddress` từ CSV, kiểm tra `orderId > 0`.

### Dữ liệu kiểm thử (`data/e2e_test_data.csv`)

- **Nguồn dữ liệu:** 120 tài khoản fixture độc lập (`hw05.vu0001@example.test` … `hw05.vu0120@example.test`) được seed vào SQLite cô lập qua `./scripts/reset_db.sh` và ghi ra `data/e2e_test_data.csv` (121 dòng gồm header).
- **Cơ chế cấp phát:** `SharedArray` parse CSV ở init context; mỗi VU dùng `rows[vuOffset + __VU - 1]` (mặc định `VU_OFFSET=0`), **không modulo**, dừng ngay trước khi chạy nếu số tài khoản < `max(40, peak VUs)`.
- **Tồn kho:** N/A (schema `products` không có cột stock).

### Ma trận cấu hình các kịch bản (sau khi hiệu chỉnh)

*Lưu ý: Các ngưỡng `P95_MS`, `ERROR_RATE`, `PEAK_VUS` và `think-time` là giả định ban đầu dùng để kiểm chứng bằng thực nghiệm, không phải kết luận năng lực phần cứng trước khi đo.*

| Kịch bản | Executor | VUs / Stages | Think-time | Thresholds mặc định | Định dạng Report View |
|---|---|---|---|---|---|
| **Load** (`23120367_Load_20261116.js`) | `ramping-vus` | `0 → 10 (30s) → 10 (2m) → 0 (30s)` | `1s ± 50%` jitter (`0.5s–1.5s`) | `p(95) < 500ms` (step & HTTP), `flow_processing_ms p(95) < 2500ms`, error `<= 0.5%`, `checks >= 99.5%`, `flow_completed > 0` | Built-in Web Dashboard (`reports/load/load_dashboard.html`) |
| **Stress** (`23120367_Stress_20261116.js`) | `ramping-vus` | `0 → 30 (30s) → 60 (45s) → 90 (45s) → 120 (1m) → 120 (1m) → 0 (30s)` | `1s ± 50%` jitter (`0.5s–1.5s`) | `p(95) < 1500ms`, `flow_processing_ms p(95) < 7500ms`, error `<= 1%`, `checks >= 99%`, `flow_completed > 0` | `handleSummary` + `k6-reporter` 3.0.4 classic tabbed HTML (`reports/stress/stress_summary.html`) |
| **Spike** (`23120367_Spike_20261116.js`) | `ramping-vus` | `0 → 10 (30s) → 120 (1s) → 120 (30s) → 10 (1s) → 10 (1m) → 0 (10s)` | `1s ± 50%` jitter (`0.5s–1.5s`) | Như Stress + `http_req_duration{phase:baseline} p(95) < 1500ms`, `http_req_duration{phase:recovery} p(95) < 1500ms`, `recovery_requests > 0` | Custom `spikeReport` HTML (`reports/spike/spike_breakdown.html`) |
| **Soak** (`23120367_Soak_20261116.js`, bổ sung) | `constant-vus` | `10 VUs` liên tục `600s` (10 phút; hợp lệ `600–900s`) | `1s ± 50%` jitter (`0.5s–1.5s`) | Như Load (`p(95) < 500ms`, error `<= 0.5%`) | Built-in Web Dashboard (`reports/soak/soak_dashboard.html`) |

---

### Các phần AI làm sai / thiếu sót, lý do AI mắc lỗi và kết quả khắc phục (Human Review)

Trong quá trình rà soát (`Human Review`) các script k6 do AI sinh tự động ban đầu (`workflow.js`, `csv.js`, `reports.js`, `23120367_*_20261116.js`) và đối chiếu trực tiếp với mã nguồn `backend/server.js`, `backend/database.js`, đã phát hiện các sai sót/thiếu sót sau và tiến hành sửa đổi:

| Hạng mục / Vị trí | Lỗi / Thiếu sót của script AI sinh ban đầu | Lý do AI mắc lỗi (nguyên nhân gốc rễ) | Hướng đã sửa & cải thiện |
|---|---|---|---|
| **1. Peak VUs và dữ liệu CSV chưa đủ gây áp lực** (`workflow.js`, `perf.config.json`, `e2e_test_data.csv`) | Script ban đầu đặt `PEAK_VUS = 40` và chỉ sinh `40` dòng CSV. Ở mức 40 VUs với think-time 5s/vòng (~8 req/s), chưa đủ gây áp lực để tìm ngưỡng bão hòa trên máy local. | AI dùng cấu hình an toàn tối thiểu (`accounts = 40`) theo giá trị khởi tạo mặc định của template thay vì cân nhắc công suất xử lý thực tế và phân biệt giữa ngưỡng Smoke/Load với tải phá hủy Stress/Spike. | Nâng `PEAK_VUS` mặc định lên **120 VUs**, tăng `"accounts": 120` trong `perf.config.json` và chạy `./scripts/reset_db.sh` sinh **120 tài khoản độc lập** vào `e2e_test_data.csv`; bổ sung bậc tăng tải 4 nấc (`30 → 60 → 90 → 120`) cho Stress và rút đỉnh Spike mặc định xuống `30s` (`SPIKE_HOLD`). |
| **2. Xử lý tài khoản bị khóa `403` & ẩn log lỗi** (`workflow.js`) | Khi tài khoản bị khóa (`403`), VU không dừng mà tiếp tục gửi `POST /api/login` ở mọi iteration còn lại; console chỉ log `__ITER === 0` nên che mất lần khóa xảy ra ở lần sai thứ 2 (`__ITER === 1`). | AI giả định dữ liệu CSV luôn đúng nên không xử lý trạng thái tài khoản bị khóa; đồng thời không tính đến logic đặc thù của SUT (`login_attempts + 2 >= 3`, khóa ngay ở lần sai thứ 2). | Thêm counter `auth_locked_errors`, đánh dấu `accountLocked = true` ở cấp VU khi nhận `403` để ngưng gọi login rác ở các iteration sau, và mở rộng log lỗi lên `__ITER <= 1`. |
| **3. Check kép làm méo tỷ lệ `checks` & cardinality** (`workflow.js`, `reports.js`) | Gọi 2 hàm `check()` độc lập trên cùng 1 response (`HTTP status ${status}` và `${name}: HTTP and business result`). Nếu API trả `200 {}`, check 1 vẫn pass và check 2 fail → tỷ lệ `checks` tính thành 50% thay vì 0%; tạo tên check động theo status làm tăng cardinality. | AI kết hợp kỹ thuật đếm HTTP status vào tên `check()` để tiện đọc trong `spikeReport` mà bỏ qua hệ quả toán học lên metric `checks` dùng trong `thresholds`. | Gộp còn **1 `check()` duy nhất** cho mỗi request (vừa HTTP vừa business body); dùng bộ `Counter` cố định `http_status_*` (`0, 200, 201, 400, 401, 403, 404, 500, other`) để thống kê status chính xác trong `spikeReport`. |
| **4. Lỗi gán nhãn pha `recovery` của Spike** (`workflow.js:69-73`) | Hàm `phase()` hardcode `elapsed >= 92 ? 'recovery' : elapsed >= 30 ? 'spike' : 'baseline'`. Mốc 92s vừa không tự cập nhật nếu đổi thời gian stage, vừa gán nhầm cả 10s ramp-down về 0 (`152s–162s`) vào pha `recovery`. | AI tính nhẩm mốc tích lũy bằng tay theo duration mặc định rồi hardcode vào hàm `phase()`, quên tách pha cuối (`target: 0`). | Tính mốc thời gian động trực tiếp từ cấu hình `spikeStageDefs`, tách riêng pha `'ramp_down'` cho giai đoạn hạ VU về 0, và bổ sung threshold cho `http_req_duration{phase:baseline}` để đối chiếu trực tiếp với `phase:recovery`. |
| **5. Kiểm tra kiểu dữ liệu `price` và ghi nhận lỗi SUT** (`workflow.js`, `csv.js`) | `Number(b.price)` chấp nhận cả `boolean` (`Number(true) === 1`); không có metric ghi nhận thực tế rằng ID chẵn trả `price` dạng `string`; `csv.js` chưa cảnh báo ký tự `'` dễ làm lỗi SQLite ở route `GET /api/products?search=` do SUT ghép chuỗi SQL. | AI chỉ tập trung chống crash script (`Number(...)`) mà không lưu dấu hiệu bất thường kiểu dữ liệu để phục vụ phân tích lỗi SUT, và bỏ qua lỗ hổng SQL ghép chuỗi ở backend. | Siết kiểm tra kiểu cho `b.price` (loại `boolean`, chuỗi rỗng, `null`) và `b.name.trim()`; thêm counter `price_string_anomalies` đếm số lần `typeof product.price === 'string'`; kiểm tra thêm cấu trúc JWT 3 phần và `user.id` tại `login`; chặn ký tự SQL nguy hiểm `'` / `;` trong `csv.js`. |
| **6. Think-time cố định & gộp vào `flow_duration_ms`** (`workflow.js`) | Dùng `sleep(1)` cố định ở 5 điểm gây đồng bộ nhịp (lock-step) giữa các VU; `flow_duration_ms` cộng cả ~4000ms `sleep` khiến khó nhìn ra độ trễ xử lý thuần túy của server. | AI chọn `sleep(think)` đơn giản và đo tổng `Date.now() - started` mà không tách thời gian chờ phía client khỏi thời gian phản hồi phía server. | Thêm random jitter `±50%` quanh `THINK_SECONDS` (có thể tắt bằng `JITTER=0`) và bổ sung metric `flow_processing_ms` (đã trừ tổng thời gian `sleptMs`) bên cạnh `flow_duration_ms`. |
| **7. Ngưỡng `thresholds` quá lỏng cho `Load`/`Soak`** (`workflow.js`) | Dùng chung `P95_MS=1500` và `ERROR_RATE=0.01` cho mọi kịch bản, khiến các API trên `127.0.0.1` dù chậm tới `1.4s` ở tải nhẹ 10 VUs vẫn vượt ngưỡng. | AI đặt một budget khởi đầu chung cho cả 4 kịch bản để tránh false positive mà không phân biệt mục tiêu của Load/Soak (tải bình thường) với Stress/Spike (tải cực hạn). | Phân tầng mặc định: `Load`/`Soak` dùng `p(95) < 500ms` và `error <= 0.5%`; `Stress`/`Spike` giữ `p(95) < 1500ms` và `error <= 1%` (vẫn cho phép ghi đè qua `P95_MS`, `ERROR_RATE`). |
| **8. Báo cáo Spike gây hiểu nhầm `group()` & mất summary `stdout`** (`reports.js`, `Stress`, `Spike`) | `spikeReport` đặt tiêu đề cột là `group()` nhưng đọc dữ liệu `step_*_ms` (HTTP timing); gộp status `0` (network/timeout) chung với `>=400`; `handleSummary` của `Stress` và `Spike` làm mất summary trên terminal; `Load`/`Soak` không ghi chú phụ thuộc env dashboard. | AI ưu tiên xuất file HTML tối giản từ `handleSummary` nên bỏ qua `stdout` mặc định của k6 và dùng nhãn cột tắt `group()` thay vì tên metric thật. | Cập nhật `reports.js`: đổi nhãn rõ `Step / Group (step_*_ms)`, tách riêng `Status 0 (Network / Timeout)` với `4xx`/`5xx`, bổ sung cột `Pass / Fail` nghiệp vụ, bảng so sánh `Baseline / Spike / Recovery`, và hàm `formatConsoleSummary` in tóm tắt ra `stdout` cho cả Stress và Spike; bổ sung hướng dẫn env `K6_WEB_DASHBOARD` trong `Load`/`Soak`. |
| **9. Hỗ trợ phân vùng VU khi chạy nhiều runner** (`workflow.js`) | `rows[__VU - 1]` mặc định chạy từ index `0`, không hỗ trợ offset nếu phân tán trên nhiều runner. | Thiết kế ban đầu giả định chỉ chạy 1 tiến trình k6 local duy nhất. | Bổ sung biến môi trường tùy chọn `VU_OFFSET` (mặc định `0`) và kiểm tra `rows.length >= vuOffset + maxVUs`. |

### Kiểm chứng sau chỉnh sửa (Smoke trên backend cô lập)

- `k6 inspect` hợp lệ trên `Load`, `Spike`, `Soak` (riêng `Stress` cần chạy `python3 scripts/perf.py install` để tải `scripts/lib/vendor/k6-reporter.js` trước khi inspect/run).
- `./scripts/run.sh Load --smoke` (1 VU, 1 iteration): `5/5` checks đạt (`100%`), `flow_completed = 1`, `flow_processing_ms = 17ms`, `http_status_200 = 5`, `error_rate = 0.0` (xem [Smoke_Load.analysis.md](../analysis/Smoke_Load.analysis.md)).
- `./scripts/run.sh Spike --smoke` (chạy trước khi tách counter status): `1/1` iteration đạt (`error_rate = 0.0`, xem [Smoke_Spike.analysis.md](../analysis/Smoke_Spike.analysis.md)).
- **Giới hạn kiểm chứng:** Smoke chỉ kiểm tra 1 VU / 1 iteration; chưa đo full Load/Stress/Spike/Soak ở mức tải thực tế (10–120 VUs).

---

## 3. Kết quả đo tải và Tài nguyên hệ thống *(Chờ chạy thực nghiệm)*

> [!IMPORTANT]
> Chưa có kết quả full scenario. Khi chạy thực nghiệm vào ngày chạy thật, bootstrap workspace mới (hoặc cập nhật ngày plan trùng `Asia/Ho_Chi_Minh`), chạy `python3 scripts/perf.py install`, `./scripts/reset_db.sh`, rồi chạy tuần tự từng kịch bản và điền số liệu trích xuất từ `raw_logs/*_raw.csv` + `analysis/*.analysis.json` + `evidence/*_resources.csv`.

Với mỗi kịch bản **Load / Stress / Spike**, cần ghi đầy đủ:
- Lệnh chạy thực tế, tên file, ngày giờ bắt đầu/kết thúc, commit hash, `SHA256` của raw CSV, JSON summary, file HTML, `CPU%/RSS` backend, ảnh chụp màn hình (`Terminal + Activity Monitor` cùng khung hình).
- Latency theo từng endpoint và tổng hợp HTTP (`min`, `avg`, `med`, `p90`, `p95`, `p99`, `max` tính bằng **ms**, phân vị Type-7), `flow_duration_ms`, `flow_processing_ms`, **HTTP RPS** tách biệt với **completed checkouts/s**, tỷ lệ lỗi HTTP (`0..1`) tách biệt với tỷ lệ lỗi flow.
- Nếu gặp `exit code 99` (threshold breach), giữ nguyên log và phân tích nguyên nhân, không đổi tên thành pass.
- Ghi chú rõ khác biệt giữa native k6 `.csv` và `.jtl` của JMeter trong đề bài (kèm xác nhận của TA; không đổi đuôi file `.csv` thành `.jtl`).

---

## 4. Ngưỡng chịu tải bền vững (Endurance / Soak Threshold) *(Chờ chạy thực nghiệm)*

- Chạy `SOAK_VUS=10 SOAK_SECONDS=600 ./scripts/run.sh Soak --pause-for-evidence` (duy trì 10–15 phút, **không reset giữa lúc đo**).
- Định nghĩa tiêu chí ổn định (hành vi p95, error rate, xu hướng tăng RAM RSS theo thời gian do `userCarts` không được xóa sau checkout).
- Phân biệt rõ **highest verified sustained load** (mức tải bền vững cao nhất đã kiểm chứng) với **stress ceiling** (ngưỡng suy giảm/điểm gãy), không suy diễn trần tối đa từ một mức pass đơn lẻ.

---

## 5. Đối chiếu phân tích AI và săn lỗi diễn giải (AI Misinterpretation Hunt) *(Chờ sau khi có raw logs full)*

- Liên kết tới [ai-verification.md](../templates/ai-verification.md) (chuyển sang `analysis/ai-verification.md` sau khi hoàn tất).
- Ghi nhận phân tích đầu tiên của AI trên raw CSV trước khi sửa, đối chiếu lại từng metric bằng `analyze_raw.py` và đánh giá tính khả thi của các đề xuất tối ưu dựa trên mã nguồn SQLite thực tế (`database.js`, `server.js`).

---

## 6. Lỗi và vấn đề hiệu năng phát hiện được *(Chờ tái hiện thực nghiệm)*

- Ghi nhận các bug/bottleneck đã thực sự tái hiện khi chạy tải (kèm bước tái hiện, môi trường, hành vi kỳ vọng/thực tế, ảnh chụp và GitHub Issue URL). Không khẳng định lỗi chưa tái hiện như kết quả đã xác nhận.

---

## 7. Kết luận và Đề xuất Continuous Performance Testing

- Tích hợp quy trình từ [continuous-performance.md](../templates/continuous-performance.md) (flowchart CI/CD, ngưỡng p95 baseline & regression gate, chi phí hạ tầng/thời gian chạy và chiến lược giảm false alarm).

---

## 8. Video minh họa và Agent Skill

- Link YouTube Unlisted tổng thời lượng `>= 6 phút`, thuyết minh giọng tiếng Việt của sinh viên, quay `Terminal + Activity Monitor` trong cùng khung hình.
- Minh họa sử dụng skill `.agents/skills/eshop-k6-performance/` từ đầu đến cuối quy trình và liệt kê đầy đủ ghi công thư viện (`benc-uk/k6-reporter` 3.0.4).

---

## 9. Phụ lục bắt buộc

- **AI Audit Report:** `audit/ai-audit.md` + `audit/ai-audit.pdf` (ghi đầy đủ tool/model, thời gian có timezone, prompt, final response hiển thị cho người dùng, human review; không ghi suy nghĩ nội bộ hay tool trace).
- **AI Critique:** `audit/ai-critique.md` + `audit/ai-critique.pdf` (một đoạn văn **200–300 từ** do chính sinh viên viết về sai sót/thiên lệch của AI và bài học phối hợp).
- **Git Commit Log:** `evidence/git-log.txt` và kiểm tra trực quan các bản PDF (`main-report.pdf`, `ai-audit.pdf`, `ai-critique.pdf`).
