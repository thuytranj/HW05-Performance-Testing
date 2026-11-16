# Kiến trúc và cấu trúc thư mục project

Project chứa mã nguồn EShop (`eshop-sut`) và công cụ thực hiện HW05 Performance Testing bằng k6. Tài liệu này phân biệt **cấu trúc đang có** với **workspace kiểm thử được sinh khi chạy skill**; các đường dẫn kết quả bên dưới chưa đồng nghĩa đã có kết quả thực thi.

## 1. Cấu trúc hiện tại

```text
HW05-Performance-Testing/
├── AGENTS.md                         # Quy tắc làm việc dành cho agent
├── README.md                         # Tài liệu ứng dụng EShop hiện có
├── api_specification.md              # Tài liệu API; cần đối chiếu implementation
├── setup_guide.md                    # Hướng dẫn thiết lập ứng dụng
├── docker-compose.yml               # Backend + web + admin
├── run_servers.sh                   # Script cũ; có killall node, xem lưu ý bên dưới
├── .env.example                     # Ví dụ cấu hình frontend API URL
├── .gitignore
├── skills-lock.json                 # Thông tin các skill đã cài
├── backend/
│   ├── server.js                     # Express routes, auth middleware, giỏ RAM
│   ├── database.js                   # SQLite schema và seed khi khởi động
│   ├── database.sqlite               # Database ứng dụng gốc
│   ├── test_profile.js               # Script kiểm tra profile có sẵn
│   ├── package.json
│   ├── package-lock.json
│   └── Dockerfile
├── frontend-web/                    # React + Vite: giao diện khách hàng
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── config.js
│   │   ├── context/                  # AuthContext, CartContext
│   │   └── pages/                    # Login, Home, ProductDetail, Cart, Checkout...
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── frontend-admin/                  # React + Vite: giao diện quản trị
│   ├── src/                         # App.jsx, main.jsx, styles và assets
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── frontend-mobile/                 # React Native + Expo
│   ├── App.js
│   ├── index.js
│   ├── app.json
│   └── package.json
├── docs/
│   ├── 2026.HW05.Performance Testing_En.pdf
│   └── architecture.md              # Tài liệu này
└── .agents/skills/
    ├── k6/
    ├── performance-testing/
    ├── test-data-management/
    ├── ci-cd-integration/
    └── eshop-k6-performance/         # Skill riêng của bài tập
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── scripts/bootstrap.py     # Discovery và sinh workspace
        ├── references/
        │   ├── hw05-checklist.md    # Ma trận yêu cầu đề và bằng chứng
        │   └── implementation.md    # Adapter, cách đo, giới hạn và validation
        ├── assets/workspace/
        │   ├── scripts/             # Runtime, runner, analyzer và workflow dùng chung
        │   └── templates/           # Báo cáo, README, bảng kiểm chứng và links
        └── tests/test_tools.py
```

Cây trên lược bỏ `.git/`, dependency directories, lockfile của frontend và một số file cấu hình/asset để dễ đọc; không phải danh sách đầy đủ mọi file.

## 2. Thành phần và luồng dữ liệu

| Thành phần | Công nghệ / nơi xử lý | Vai trò |
|---|---|---|
| Backend | Node.js, Express, `sqlite3`, JWT | REST API, xác thực, catalog và tạo đơn |
| Database | SQLite, `backend/database.sqlite` | Users, products, categories, orders, coupons, coupon usage |
| Giỏ hàng | Object `userCarts` trong tiến trình Node | Dữ liệu giỏ theo user, mất khi restart |
| Web / Admin | React + Vite | Gọi API backend; không nằm trong tải browser của HW05 này |
| Mobile | React Native + Expo | Client ứng dụng; ngoài workflow tải API đã chọn |
| k6 | Các plan được sinh trong workspace | Tạo tải HTTP E2E và xuất metrics |
| Python helpers | Skill và workspace | Discovery, seed fixture, quản lý runtime, phân tích log và audit |

Docker Compose ánh xạ backend `3000:3000`, web `5173:5173`, admin `5174:5174`. Backend hiện hardcode port `3000`; cấu hình frontend mặc định trỏ tới `http://localhost:3000/api`. Đây là cấu hình trong source, không phải bằng chứng các service đang chạy.

Workflow HW05 sử dụng trực tiếp API:

```text
k6 VU + một tài khoản CSV độc lập
  → POST /api/login                       [Auth-heavy]
  → GET  /api/products?search=<keyword>    [Read-heavy]
  → GET  /api/products/<id>                [Read-heavy]
  → POST /api/cart                        [Transactional]
  → POST /api/checkout                    [Transactional]
  → raw CSV + JSON summary + HTML report
  → phân tích số liệu + sinh viên kiểm chứng kết luận AI
```

JWT lấy từ field `token` của login response và truyền bằng `Authorization: Bearer <token>`. Load, Stress, Spike dùng cùng workflow; profile tạo tải và cách trình bày report khác nhau.

### Những đặc tính ảnh hưởng phép đo

- `database.js` xóa bảng và seed lại khi được import. Khởi động/restart backend gốc có thể làm mất dữ liệu gốc.
- `run_servers.sh` gọi `killall node`; không dùng script này cho quy trình đo hiệu năng.
- Login sai tăng `login_attempts` thêm **2**, khóa khi `>=3` trong **180000 ms**. Cần phân biệt implementation này với yêu cầu ba lần sai trong đề.
- Checkout hiện không xóa giỏ RAM, không lưu order items và tin `total_amount` phía client; diễn giải kết quả theo đúng phạm vi đó.
- Products chưa có cột tồn kho. Không tạo SQL reset stock hoặc kết luận stock depletion cho revision này.
- Product không tồn tại có thể trả HTTP 200 với `{}`; phải kiểm tra cả body và nghiệp vụ.

## 3. Cấu trúc workspace bài tập

Mặc định dùng `performance/` ở gốc project. **Thư mục này chỉ được tạo khi bootstrap**, không được tạo file kết quả giả để lấp đầy cấu trúc. `<ID>` mặc định `23120367`; `<DATE>` là ngày chạy thực tế `YYYYMMDD` theo `Asia/Ho_Chi_Minh`.

```text
performance/
├── perf.config.json                     # ID, ngày, port, số account, source hashes
├── .gitignore                           # Bỏ runtime, vendor, Python cache
├── README.md                            # Tự chấm + tóm tắt; tạo từ template rồi điền
├── data/
│   ├── api_discovery.json
│   ├── e2e_test_data.csv                 # >=40 dòng, chỉ sinh sau reset/seed thực tế
│   ├── seed_snapshot.json
│   └── dependencies.json                # Phiên bản/checksum dependency đã tải
├── scripts/
│   ├── <ID>_Load_<DATE>.js
│   ├── <ID>_Stress_<DATE>.js
│   ├── <ID>_Spike_<DATE>.js
│   ├── <ID>_Soak_<DATE>.js
│   ├── perf.py                          # install / reset / run / stop
│   ├── reset_db.sh
│   ├── run.sh
│   ├── collect_hardware.sh
│   ├── analyze_raw.py
│   ├── analyze_resources.py
│   ├── record_audit.py
│   ├── check_submission.py
│   └── lib/
│       ├── workflow.js                  # Flow, options, checks và metrics dùng chung
│       ├── csv.js                       # Parser CSV có hỗ trợ quoted fields
│       ├── reports.js                   # Custom report cho Spike
│       └── vendor/                      # Reporter tải khi install; không track
├── raw_logs/
│   ├── <ID>_<Scenario>_raw.csv           # Raw samples đầy đủ
│   ├── <Scenario>_summary.json           # Aggregate; không thay raw log
│   └── <Scenario>_run.json               # Command, thời gian, hashes, exit code
├── reports/
│   ├── api_discovery.md
│   ├── main-report.md                   # Sinh viên hoàn thiện và xuất PDF
│   ├── main-report.pdf
│   ├── continuous-performance.md        # Flowchart + p95 regression + trade-offs
│   ├── load/load_dashboard.html         # Built-in Web Dashboard
│   ├── stress/stress_summary.html       # k6-reporter, dạng tab
│   ├── spike/spike_breakdown.html       # Group latency + HTTP status counts
│   ├── soak/soak_dashboard.html
│   └── smoke/                           # Smoke output riêng, không thay full run
├── analysis/
│   ├── <Scenario>.analysis.json
│   ├── <Scenario>.analysis.md
│   └── ai-verification.md               # Giá trị raw đối chiếu nhận định AI
├── evidence/
│   ├── events.jsonl                     # Install, seed, reset và run events
│   ├── runtime-adaptation.json          # Khác biệt port/bind của bản backend copy
│   ├── <Scenario>_resources.csv          # Backend PID, CPU, RSS thực tế
│   ├── <Scenario>_screen.png            # Chụp tool + monitor cùng khung hình
│   ├── hardware.txt
│   ├── hardware.png
│   ├── git-log.txt
│   └── links.json                       # Public repo, video, issues, xác nhận raw format
├── audit/
│   ├── ai-audit.md                      # Mỗi lượt: tool, thời gian, prompt, final response
│   ├── ai-audit.pdf
│   ├── ai-critique.md                   # Sinh viên viết một đoạn 200–300 từ
│   └── ai-critique.pdf
├── templates/                           # Bản mẫu, chưa phải deliverables hoàn chỉnh
│   ├── README.md
│   ├── main-report.md
│   ├── continuous-performance.md
│   ├── ai-verification.md
│   └── links.json
└── .runtime/                            # Chỉ local; không đưa vào bài nộp
    ├── backend/                         # Bản copy backend, DB và node_modules cô lập
    ├── backend.pid
    ├── backend.log
    └── run.lock                         # Có trong lúc runner đang đo tải
```

`<Scenario>` trong kết quả full run là `Load`, `Stress`, `Spike`, `Soak`. Smoke dùng tên `Smoke_Load`, `Smoke_Stress`, `Smoke_Spike`; smoke dashboard có thể không xuất HTML do thời lượng quá ngắn. Một số file trong cây chỉ xuất hiện sau install, reset, chạy test, chụp ảnh hoặc hoàn thiện báo cáo.

Khi cần đo lại, dùng workspace mới, ví dụ `performance-runs/<DATE>_<label>/`, bằng `--output`. Giữ nguyên workspace cũ; không ghi đè raw logs, HTML hay manifest. Đây là quy ước tổ chức thêm của project, không phải naming convention bắt buộc của đề.

## 4. Cách sinh và sử dụng cấu trúc

AI Audit chỉ cần `audit/ai-audit.md` và bản PDF khi nộp; không cần thư mục `interactions/` hay file `interactions.jsonl`. Mỗi tương tác vẫn ghi tool/model, thời gian, prompt và final response của lượt đó; không ghi suy nghĩ nội bộ, cập nhật tiến độ hoặc tool traces. Raw logs test được giữ riêng đầy đủ. Nếu có archive cũ, chỉ bỏ các bản trùng sau khi kiểm tra nội dung cần thiết đã nằm trong Markdown và không còn link phụ thuộc.

Từ project root:

```bash
python3 .agents/skills/eshop-k6-performance/scripts/bootstrap.py \
  --project . --output performance --student-id 23120367 --accounts 40
cd performance
python3 scripts/perf.py install
./scripts/reset_db.sh
./scripts/run.sh Load --smoke
```

Bootstrap cần output trống. Dùng `--port 3100` nếu cổng gốc đang được sử dụng. Install tải dependency; reset chỉ chạy bản backend cô lập. Trước đo full, review parameters và chuẩn bị quay/chụp bằng chứng. Lệnh chạy từng scenario, suite, phân tích plateau và audit nằm trong [skill](../.agents/skills/eshop-k6-performance/SKILL.md).

Không chạy ngay `run.sh all` sau smoke thủ công trong cùng workspace: suite có bước smoke riêng và từ chối ghi đè output đã có. Chọn chạy thủ công các full scenario hoặc bootstrap workspace mới cho suite.

## 5. Trách nhiệm và quy tắc lưu trữ

| Khu vực | Trách nhiệm | Cách lưu |
|---|---|---|
| `backend/`, các frontend | SUT gốc, nguồn kiểm chứng API | Giữ nguyên khi chỉ làm bài performance; thay đổi phải được giao và ghi nhận |
| `.agents/skills/eshop-k6-performance/` | Quy trình tái sử dụng và template gốc | Commit cùng project; sửa khi cần thay đổi quy trình cho các lần sinh sau |
| `performance/scripts/`, `data/` | Plans và input của lần đo cụ thể | Track cấu hình, CSV fixture và source hashes; ghi rõ chỉnh sửa sau bootstrap |
| `raw_logs/`, `reports/`, `analysis/`, `evidence/`, `audit/` | Bằng chứng và báo cáo của lần đo | Giữ cả run fail; phân biệt dữ liệu gốc, số liệu tính lại và nhận định |
| `templates/` | Mẫu để điền | Không tính là báo cáo đã hoàn thành |
| `.runtime/`, `node_modules/`, `scripts/lib/vendor/` | Môi trường tái tạo được | Không commit; vendor có URL/version/checksum và có thể tải lại |

Sửa asset trong skill không tự cập nhật workspace đã sinh. Sửa một workspace cũng không tự cập nhật skill. Nếu thay source SUT, bootstrap workspace mới sau discovery và giữ bằng chứng của revision trước.

## 6. Hồ sơ nộp bài

ZIP đặt tên `<StudentID>_HW05_AI_Performance_<SelfAssessedGrade>.zip`, điểm ba chữ số `000..100` do sinh viên tự đánh giá. Gốc ZIP nên có README tóm tắt và giữ các đường dẫn tương đối của workspace để liên kết báo cáo còn hoạt động.

Đưa vào ZIP: plans và shared libraries, CSV, full raw logs, summaries/manifests, các thư mục HTML, analysis, screenshots/hardware/spec table, main report Markdown+PDF, AI Audit/Critique Markdown+PDF, continuous-testing proposal, Git log, public repo/video/issue links và bộ custom skill. Nếu không đóng gói vendor thì giữ thông tin dependency và hướng dẫn `perf.py install` để tái tạo. Loại `.runtime/`, `.env`, `node_modules/` và cache.

Video phải unlisted, tổng ít nhất 6 phút, tự thuyết minh tiếng Việt, tool và backend monitor cùng khung hình; kèm đoạn demo skill end-to-end. README có bảng tự chấm `30/20/20/10/10/10`, các scenario đã chạy, nhóm endpoint, ngưỡng soak bằng số và số issue thực tế.

Đề cho dùng k6 nhưng liệt kê raw `.jtl` theo JMeter: giữ native CSV và ghi nhận/xác minh với TA; không đổi đuôi CSV để giả log JMeter. Chạy `python3 scripts/check_submission.py` từ workspace rồi kiểm tra nội dung bằng tay; checker không chứng thực video, giọng nói, human review hay chất lượng PDF.

## 7. Nguồn tham chiếu

- [Đề HW05](2026.HW05.Performance%20Testing_En.pdf).
- [Quy tắc cho agent](../AGENTS.md).
- [Skill riêng](../.agents/skills/eshop-k6-performance/SKILL.md).
- [Checklist đối chiếu đề](../.agents/skills/eshop-k6-performance/references/hw05-checklist.md).
- [Backend API implementation](../backend/server.js), [database và seed](../backend/database.js).
