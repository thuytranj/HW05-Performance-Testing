# AI Verification & Misinterpretation Hunt (Task 2)

- **Workspace:** `performance_250/`
- **Raw CSV & SHA256 đối chiếu:**
  - `raw_logs/23120367_Load_raw.csv` (`a78c552b144202b0d1082e67db7f977c24c7109e88f51f48209b521a9486f61e`)
  - `raw_logs/23120367_Stress_raw.csv` (`43283b655b6172410c6f5637e794e5d6bd81e57212964dd9b7eabb8cb1fa9878`)
  - `raw_logs/23120367_Spike_raw.csv` (`1c89c7a4cf73814ef1d3092447e30681e5bcbd4558f47b72c052368d0c6212cc`)
  - `raw_logs/23120367_Soak_raw.csv` (`ec67cb4c41df587980a34759fa86ffd844c4cc14a95490452f235c728c23fec9`)
- **Công cụ đối chiếu độc lập:** `scripts/analyze_raw.py` (Type-7 linear quantiles, `ms`, `error_rate` dạng `0..1`), `scripts/analyze_resources.py`.
- **Lưu ý kiến trúc SUT thực tế:** `eshop-sut` sử dụng **SQLite** (`backend/database.js`, `sqlite3`) cho `users`, `products`, `categories`, `orders`, `coupons`; chỉ riêng giỏ hàng (`userCarts`) được lưu **in-memory trên RAM** tiến trình Node.js (`backend/server.js:14`).

---

## 1. Đối chiếu phân tích đầu tiên của AI với Raw CSV Log

Phân tích đầu tiên của AI đọc trực tiếp từ `analysis/*.analysis.md`, `evidence/*_resources.analysis.json`, `backend/server.js` và `backend/database.js`. Không bịa đặt lỗi: các con số tổng hợp AI trích xuất khớp với `analyze_raw.py`, nhưng vẫn có điểm thiếu sót về tách pha (windowing) và bỏ sót metric bất thường dữ liệu.

| Chỉ số / Nhận định của AI | Giá trị trích xuất từ Raw CSV Log | Đánh giá | Giải thích nguyên nhân kỹ thuật |
|---|---|---|---|
| **Load** (`8.31 HTTP RPS`, `1.66 checkout/s`, `p95 = 7.24 ms`, `error = 0.0`) | `23120367_Load_raw.csv` (`a78c552b...`), `1,520` samples, cửa sổ `182.861s`: HTTP `p95 = 7.239 ms`, `rps = 8.312`, `completed/s = 1.662`, `error_rate = 0.0` | **Chính xác** | AI trích đúng số liệu Type-7 từ `Load.analysis.md`, tách đúng HTTP RPS với completed checkout/s và giữ đơn vị `ms`. |
| **Stress** (`162.55 HTTP RPS`, `32.51 checkout/s`, `p95 = 8.56 ms`, `p99 = 12.38 ms`, `0%` lỗi) | `23120367_Stress_raw.csv` (`43283b65...`), `44,360` samples, cửa sổ `272.895s`: HTTP `p95 = 8.556 ms`, `p99 = 12.379 ms`, `rps = 162.553`, `completed/s = 32.511`, `error = 0.0` | **Chính xác (có ghi chú thận trọng)** | Số liệu chuẩn xác; AI cũng nhận định đúng rằng `0%` lỗi ở 250 VUs chưa phải là ngưỡng trần tối đa (breaking point). |
| **Spike** (`67.65 HTTP RPS` toàn cửa sổ, `p95 = 7.90 ms`, `p99 = 11.78 ms`) | `23120367_Spike_raw.csv` (`1c89c7a4...`), `9,185` samples, cửa sổ `135.780s`: HTTP `p95 = 7.901 ms`, `rps = 67.646`. Trong `Spike_summary.json`: `baseline p95 = 8.274 ms`, `recovery p95 = 8.545 ms` | **Thiếu tách pha (Incomplete windowing)** | Số trung bình toàn run đúng, nhưng AI chưa tách riêng pha `baseline`, pha đỉnh `spike` (30s ở 250 VUs) và pha `recovery` nên không phản ánh RPS đỉnh thực sự trong cú sốc tải. |
| **Soak** (`19.78 HTTP RPS`, `p95 = 8.18 ms`, RSS `+38.44 MiB` trong `605.3s`) | `23120367_Soak_raw.csv` (`ec67cb4c...`), `11,975` samples, `605.298s`; `Soak_resources.analysis.json`: `47.72 → 86.16 MiB` (`+38.44 MiB`, peak `90.00 MiB`) | **Chính xác (chưa tách warm-up vs steady-state)** | Số liệu khớp hoàn toàn và AI thận trọng không kết luận vội memory leak chỉ từ RSS, nhưng chưa tách nửa đầu vs nửa sau Soak để kiểm tra độ trôi `p95` theo thời gian. |
| **Nút thắt số 1 & 2 (`POST /api/checkout`, `POST /api/login`)** | `checkout p95`: Load `8.606`, Stress `10.624`, Spike `9.802`, Soak `9.626 ms`; `login p95`: Load `5.802`, Stress `9.114`, Spike `7.587`, Soak `7.480 ms` | **Chính xác** | Hai endpoint có thao tác ghi SQLite (`INSERT INTO orders`, `UPDATE users`) luôn có `p95`/`p99` cao nhất, nhưng ở tải đo hiện tại độ trễ vẫn dưới `15 ms`. |
| **Bỏ sót bất thường kiểu dữ liệu `price` dạng `string`** | `*_summary.json` metric `price_string_anomalies`: tổng **5,361 lần** (`Load: 123`, `Stress: 3,542`, `Spike: 743`, `Soak: 953`) | **Thiếu sót (Omission)** | AI bỏ qua metric ghi nhận lỗi không nhất quán kiểu dữ liệu ở `GET /api/products/:id` (`server.js:162`: ID chẵn trả `price` dạng `string`). |

---

## 2. Đánh giá tính khả thi của các đề xuất tối ưu hóa (Optimization Feasibility)

Đối chiếu 5 đề xuất tối ưu hóa của AI với mã nguồn thực tế (`backend/server.js`, `backend/database.js`, `backend/package.json`):

| Đề xuất thực tế của AI | Phân loại | Bằng chứng mã nguồn / Thực nghiệm | Phân tích kỹ thuật & Trade-off |
|---|---|---|---|
| **1. Xóa `userCarts[userId]` sau checkout & chuyển sang SQLite/Redis** | **Khả thi một phần (Xóa RAM: Feasible; Redis: Unverified)** | `server.js:14, 290-309`; Soak RSS tăng `+38.44 MiB` sau `2,395` checkout | `delete userCarts[userId]` (hoặc `= []`) sau `INSERT INTO orders` là sửa đơn giản, triệt tiêu tích lũy RAM. Tuy nhiên stack hiện tại không có Redis (`package.json`), đưa Redis vào làm tăng độ phức tạp hạ tầng không cần thiết cho ứng dụng đơn node. |
| **2. Bật SQLite WAL mode (`journal_mode=WAL`, `synchronous=NORMAL`, `busy_timeout=5000`)** | **Khả thi (cần đo kiểm chứng)** | `database.js:5` đang mở kết nối SQLite mặc định (rollback journal) | Cho phép đọc-ghi đồng thời và giảm contention khi mở rộng tải ghi `checkout`/`login` > 250 VUs. Trade-off: phát sinh file `-wal`/`-shm` và chưa thể hiện tác động rõ ở mức 250 VUs hiện tại (`p95 = 8.56 ms`, `0%` lỗi). |
| **3. Tạo Index `users(email)`, `orders(user_id)` & tham số hóa `search`** | **Tham số hóa: Khả thi bắt buộc; Index: Cần `EXPLAIN QUERY PLAN`** | `database.js:50-81`; `server.js:144` ghép chuỗi `LIKE '%${searchQuery}%'` | Tham số hóa query `search` là bắt buộc để tránh SQLi/lỗi `500` khi gặp ký tự `'`. Với `users(email)` và `orders(user_id)`, index hợp lý khi dữ liệu lớn nhưng trên 252 user hiện tại hiệu năng chưa khác biệt. Lưu ý: index B-tree trên `products(name)` **không** tối ưu được `LIKE '%keyword%'` (wildcard đầu); chỉ `FTS5` mới xử lý được nếu catalog lớn. |
| **4. Tránh `UPDATE users` dư thừa khi `login` thành công** | **Khả thi (Feasible)** | `server.js:46-50` luôn chạy `UPDATE users SET login_attempts = 0, locked_until = NULL` | Thêm điều kiện `if (user.login_attempts > 0 || user.locked_until !== null)` giúp loại bỏ 100% thao tác ghi DB không cần thiết ở luồng login hợp lệ, giảm khóa ghi SQLite cạnh tranh với `checkout`. |
| **5. Bounded LRU Cache + TTL cho `GET /api/products` và `:id`** | **Khả thi nhưng ưu tiên thấp (Low ROI hiện tại)** | `server.js:141-165`; `detail p95 = 7.21 ms`, `search p95 = 6.95 ms` ở Stress | Bảng `products` hiện chỉ có 5 dòng và độ trễ đọc đã rất thấp (`~2.5 ms` avg). Thêm cache phải xử lý invalidation ở cả `POST/PUT/DELETE /api/products` và `POST /api/admin/import-products` (`server.js:167-241`), dễ phát sinh bug dữ liệu cũ nếu không cần thiết. |

---

## 3. Tóm tắt Human Review cho Test Plans (Task 1)

| Lựa chọn ban đầu của AI | Sửa đổi của con người | Lý do AI bỏ sót | Bằng chứng / Commit |
|---|---|---|---|
| `PEAK_VUS = 40`, `40` accounts CSV | Nâng lên `250 VUs` (`250` accounts), `SOAK_VUS = 20` | Dùng ngưỡng mặc định tối thiểu của template, chưa đủ gây áp lực lên Apple M1 | `bfc5a4e`, `ba126e4` |
| Không dừng VU khi gặp `403` lockout; log `__ITER === 0` | Thêm `auth_locked_errors`, chặn spam khi khóa, log `__ITER <= 1` | Giả định CSV luôn hợp lệ, bỏ qua rule khóa sau **2** lần sai (`login_attempts + 2 >= 3`) | `106fe69`, `ac474c7` |
| Gọi 2 `check()` trên 1 request; `phase()` Spike hardcode `92s` | Gộp 1 `check()`, tách `http_status_*`, tính `phase()` động + `ramp_down` | Tối ưu tiện lợi cho report nhưng làm méo toán học tỷ lệ `checks` và gộp nhầm ramp-down vào `recovery` | `106fe69`, `ac474c7` |
| `perf.py` không `waitpid` trên macOS & probe không `SO_REUSEADDR` | Reap zombie `(node)`, tự dọn stale PID, bật `SO_REUSEADDR` + retry bind | Thiếu kiểm thử vòng đời tiến trình con trên macOS khi chạy liên tiếp nhiều kịch bản | `bfc5a4e` |

*(Chi tiết đầy đủ 10 điểm đã sửa xem tại Mục 2 của [main-report.md](../reports/main-report.md)).*
