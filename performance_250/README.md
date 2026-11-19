# Báo cáo tổng kết bài nộp HW05 — Performance Testing với k6

- **Họ và tên:** Trần Ngọc Diễm Thúy
- **Mã số sinh viên:** `23120367`
- **Lớp / Học phần:** Kiểm thử phần mềm
- **Ngày thực thi:** `2026-11-19` (Múi giờ: `Asia/Ho_Chi_Minh`)
- **Môi trường đo đạc:** macOS Sequoia 15.1 (Darwin 24.1.0), Apple M1, 8GB RAM. Hostname máy đo: `Thuys-MacBook-Air`.
- **Public GitHub Repository:** [https://github.com/thuytranj/HW05-Performance-Testing](https://github.com/thuytranj/HW05-Performance-Testing)

---

## 1. Bảng tự đánh giá kết quả (Self-Assessment Table)

| Tiêu chí đánh giá | Điểm tối đa | Điểm tự chấm | Minh chứng & Artifacts tương ứng |
|---|:---:|:---:|---|
| **1. Kịch bản Load Testing** | 30 | **30** | Đầy đủ 5 bước E2E; 10 VUs, 3 phút; built-in HTML dashboard tại [load_dashboard.html](reports/load/load_dashboard.html); raw CSV [23120367_Load_raw.csv](raw_logs/23120367_Load_raw.csv); phân tích [Load.analysis.md](analysis/Load.analysis.md); screenshot [Load_screen.png](evidence/Load_screen.png). |
| **2. Kịch bản Stress Testing** | 20 | **20** | Thang tải 6 giai đoạn, đỉnh 250 VUs (4m30s); k6-reporter tabbed HTML tại [stress_summary.html](reports/stress/stress_summary.html); raw CSV [23120367_Stress_raw.csv](raw_logs/23120367_Stress_raw.csv); phân tích [Stress.analysis.md](analysis/Stress.analysis.md); screenshot [Stress_screen.png](evidence/Stress_screen.png). |
| **3. Kịch bản Spike Testing** | 20 | **20** | Tải dồn 0 lên 250 VUs trong 10s, duy trì 60s và hạ tải; custom breakdown HTML tại [spike_breakdown.html](reports/spike/spike_breakdown.html); raw CSV [23120367_Spike_raw.csv](raw_logs/23120367_Spike_raw.csv); phân tích [Spike.analysis.md](analysis/Spike.analysis.md); screenshot [Spike_screen.png](evidence/Spike_screen.png). |
| **4. AI Analysis & Critique** | 10 | **10** | Lịch sử tương tác đầy đủ tại [ai-audit.md](audit/ai-audit.md); bảng kiểm chứng 4 cột đối chiếu raw samples tại [ai-verification.md](analysis/ai-verification.md); bài phản biện AI Critique chuẩn 285 từ tại [ai-critique.md](audit/ai-critique.md); 2 GitHub Issues thực tế. |
| **5. Continuous Performance (Task 3)** | 10 | **10** | Đề xuất mô hình tích hợp CI/CD hoàn chỉnh (G9.6) tại [continuous-performance.md](reports/continuous-performance.md); sơ đồ Mermaid, chiến lược lọc commit, ngân sách hồi quy `p95`, xử lý nhiễu false alarms và phân tích chi phí. |
| **6. Reusable Agent Skills** | 10 | **10** | Bộ 5 Agent Skills chuyên biệt đóng gói tại [skills/](skills/); demo trực tiếp quy trình kiểm thử tự động end-to-end trên video. |
| **TỔNG CỘNG** | **100** | **100/100** | Bài làm đầy đủ, trung thực, số liệu tính từ raw CSV Type-7, không giả mạo số liệu hay kết quả. |

---

## 2. Giới thiệu vai trò của từng Agent Skill trong dự án

Dự án tổ chức một hệ sinh thái gồm **5 Agent Skills chuyên biệt** đặt trong thư mục [skills/](skills/), hỗ trợ toàn diện từ khâu dữ liệu, công cụ k6, phương pháp luận cho đến CI/CD và thực thi bài toán EShop:

1. **`test-data-management`** ([SKILL.md](skills/test-data-management/SKILL.md)):
   - **Vai trò:** Quản lý và sinh dữ liệu kiểm thử chất lượng cao. Thiết kế tệp [e2e_test_data.csv](data/e2e_test_data.csv) chứa **250 tài khoản độc lập** (vượt xa yêu cầu tối thiểu 40 dòng của đề bài). Đảm bảo mỗi Virtual User (VU) có một tài khoản duy nhất, triệt tiêu hoàn toàn rủi ro khóa tài khoản do login đồng thời hoặc đụng độ dữ liệu giỏ hàng.

2. **`k6`** ([SKILL.md](skills/k6/SKILL.md)):
   - **Vai trò:** Cung cấp tri thức chuyên sâu về công cụ kiểm thử tải Grafana k6. Định nghĩa cấu hình các loại executor (`ramping-vus`, `constant-vus`), quản lý nhóm `group()`, các phép kiểm tra `check()`, custom metrics, và điều khiển cơ chế xuất dữ liệu raw CSV cũng như xuất báo cáo đa dạng.

3. **`performance-testing`** ([SKILL.md](skills/performance-testing/SKILL.md)):
   - **Vai trò:** Hướng dẫn phương pháp luận và chuẩn mực kiểm thử hiệu năng. Xác định rõ mục tiêu của từng kịch bản (Load đo năng lực cơ sở, Stress tìm điểm gãy, Spike kiểm tra khả năng co giãn và phục hồi, Soak kiểm tra độ bền tài nguyên), đồng thời định nghĩa các tiêu chuẩn SLA/SLO về độ trễ và tỷ lệ lỗi cho môi trường sản xuất.

4. **`ci-cd-integration`** ([SKILL.md](skills/ci-cd-integration/SKILL.md)):
   - **Vai trò:** Thiết kế giải pháp tích hợp kiểm thử hiệu năng vào quy trình CI/CD (Task 3). Cung cấp các pipeline template cho GitHub Actions và GitLab CI, thiết lập cơ chế lọc commit thông minh (chỉ chạy kiểm thử tải khi có thay đổi ở backend/database), và đặt ngưỡng chặn hồi quy hiệu năng (quality gates) dựa trên `p95`.

5. **`eshop-k6-performance`** ([SKILL.md](skills/eshop-k6-performance/SKILL.md)):
   - **Vai trò:** **Skill nòng cốt của bài tập HW05**. Đóng gói trọn vẹn quy trình 7 giai đoạn kiểm thử cho ứng dụng EShop:
     - Cô lập runtime backend Node.js và database SQLite (tránh xung đột PID và lỗi destructive seed của source gốc).
     - Quản lý runner tự động với tính năng chạy Smoke test xác minh tính toàn vẹn của token, product ID và orderId trước khi chạy tải.
     - Tự động hóa phân tích dữ liệu raw CSV bằng [analyze_raw.py](scripts/analyze_raw.py) (tính phân vị chuẩn Type-7, không tính trung bình p95 endpoint).
     - Phân tích mẫu tài nguyên hệ thống (CPU, RSS RAM) bằng [analyze_resources.py](scripts/analyze_resources.py).
     - Tự động kiểm tra tính toàn vẹn của hồ sơ nộp bài qua [check_submission.py](scripts/check_submission.py).

---

## 3. Tổng hợp kết quả thực thi các kịch bản kiểm thử

Mọi kịch bản đều thực thi luồng E2E 5 bước độc nhất không trùng lặp: `Login (lấy JWT)` $\rightarrow$ `Search sản phẩm` $\rightarrow$ `Xem chi tiết sản phẩm` $\rightarrow$ `Thêm vào giỏ hàng` $\rightarrow$ `Checkout đơn hàng`.

| Kịch bản | Số VUs tối đa | Thời lượng đo | Tổng HTTP Requests | Completed Checkouts | HTTP RPS | Checkout RPS | HTTP `p95` | Error Rate | Peak RSS (MiB) | RSS Thay đổi | Max CPU | Định dạng Báo cáo HTML |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Load** | 10 | 182.86s | 1,520 | 304 | 8.31 | 1.66 | 7.24 ms | 0.0% | 68.88 | +13.05 MiB | 10.0% | [Built-in Dashboard](reports/load/load_dashboard.html) |
| **Stress** | 250 | 272.90s | 44,360 | 8,872 | 162.55 | 32.51 | 8.56 ms | 0.0% | 105.02 | +23.00 MiB | 54.6% | [k6-reporter HTML](reports/stress/stress_summary.html) |
| **Spike** | 250 | 135.78s | 9,185 | 1,837 | 67.65 | 13.53 | 7.90 ms | 0.0% | 102.69 | +13.81 MiB | 53.0% | [Custom Breakdown](reports/spike/spike_breakdown.html) |
| **Soak** | 20 | 605.30s | 11,975 | 2,395 | 19.78 | 3.96 | 8.18 ms | 0.0% | 90.00 | **+38.44 MiB** | 23.7% | [Built-in Dashboard](reports/soak/soak_dashboard.html) |

### Ngưỡng chịu tải bền vững đo được (Endurance Threshold):
- Hệ thống duy trì ổn định ở mức **20 VUs** trong **605 giây (10 phút 5 giây)** với thông lượng **19.78 HTTP RPS** (tương đương **3.96 completed checkout/s**), độ trễ `p95` đạt **8.18 ms** và tỷ lệ lỗi giữ vững ở mức **0.0%**.
- **Cảnh báo giới hạn bộ nhớ:** Bộ nhớ RSS tăng tuyến tính từ `47.72 MiB` lên `86.16 MiB` (tăng ròng `+38.44 MiB`, đỉnh `90.00 MiB`). Điều này chứng minh SUT có điểm nghẽn tích tụ RAM và không thể duy trì tải liên tục nhiều giờ nếu không khắc phục lỗi giải phóng biến `userCarts`.

---

## 4. Các lỗi và bất thường phát hiện trên SUT (GitHub Issues)

Trong quá trình kiểm thử tải và phân tích dữ liệu raw/tài nguyên, sinh viên đã phát hiện và ghi nhận 2 lỗi kỹ thuật thực tế trên repository GitHub (Xem tài liệu chi tiết có chèn ảnh minh chứng tại [reports/bug-report.md](reports/bug-report.md)):

1. **GitHub Issue #1:** [Kiểu dữ liệu `price` không nhất quán ở `GET /api/products/:id`](https://github.com/thuytranj/HW05-Performance-Testing/issues/1)
   - *Mô tả:* Endpoint trả về giá tiền dưới dạng chuỗi (String) đối với các sản phẩm có ID chẵn (`server.js:162`), trái với schema `INTEGER` trong database và endpoint danh sách. Metric đo được ghi nhận **5,361 lần** xảy ra bất thường này qua 4 kịch bản.
2. **GitHub Issue #2:** [Tích lũy bộ nhớ RAM (`userCarts`) do `POST /api/checkout` không xóa giỏ hàng](https://github.com/thuytranj/HW05-Performance-Testing/issues/2)
   - *Mô tả:* Giỏ hàng lưu trữ vô hạn trong biến đối tượng RAM tiến trình Node.js (`server.js:14, 290–309`) và không được xóa sau khi checkout thành công, dẫn đến hiện tượng phình bộ nhớ đo được rõ ràng trong bài Soak test (+38.44 MiB).

---

## 5. Danh mục liên kết & Minh chứng thực tế (Links & Evidence)

- **Public GitHub Repository:** [https://github.com/thuytranj/HW05-Performance-Testing](https://github.com/thuytranj/HW05-Performance-Testing)
- **Video Demo kịch bản kiểm thử (>= 6 phút, giọng tiếng Việt của sinh viên):**
  - URL: [https://youtu.be/aYq1_LxL9zk](https://youtu.be/aYq1_LxL9zk)
  - Thời lượng: 380 giây (>= 6 phút).
  - Nội dung: Quay Terminal và Activity Monitor trong cùng một khung hình, thuyết minh bằng giọng thật của sinh viên, thể hiện rõ hostname `Thuys-MacBook-Air` và PID backend `node`.
- **Video Demo Agent Skill:**
  - URL: [https://youtu.be/s2V4jQMAYdg](https://youtu.be/s2V4jQMAYdg)
  - Nội dung: Trình diễn sử dụng hệ sinh thái 5 skills và demo chi tiết skill `eshop-k6-performance` từ khâu bootstrap, chạy smoke, chạy kịch bản tải, phân tích raw CSV và kiểm tra cấu trúc bài nộp bằng [check_submission.py](scripts/check_submission.py).
- **Xác nhận định dạng k6 raw CSV thay cho .jtl:**
  - Đã làm rõ sự không nhất quán giữa đề bài (cho phép dùng k6 nhưng văn bản đề cũ ghi `.jtl` của JMeter). Dự án bảo toàn toàn vẹn dữ liệu gốc bằng native k6 CSV với đầy đủ raw samples theo phân vị Type-7.
- **Danh sách báo cáo và minh chứng kỹ thuật:**
  - Báo cáo chính: [reports/main-report.md](reports/main-report.md) | [reports/main-report.pdf](reports/main-report.pdf)
  - Nhật ký tương tác AI: [audit/ai-audit.md](audit/ai-audit.md) | [audit/ai-audit.pdf](audit/ai-audit.pdf)
  - Đánh giá phản biện AI: [audit/ai-critique.md](audit/ai-critique.md) | [audit/ai-critique.pdf](audit/ai-critique.pdf)
  - Đề xuất Continuous Performance: [reports/continuous-performance.md](reports/continuous-performance.md)
  - Bảng kiểm chứng số liệu: [analysis/ai-verification.md](analysis/ai-verification.md)
  - Lịch sử Git commit chi tiết: [evidence/git-log.txt](evidence/git-log.txt)
  - Thông số phần cứng: [evidence/hardware.txt](evidence/hardware.txt) | Ảnh cấu hình [evidence/hardware.png](evidence/hardware.png)

---

## 6. Hướng dẫn tái lập môi trường (Reproduction Steps)

Để tái lập toàn bộ môi trường và kiểm chứng kết quả từ đầu:

```bash
# 1. Di chuyển vào thư mục bài tập
cd performance_250

# 2. Khởi tạo môi trường và kiểm tra trạng thái
python3 scripts/perf.py install

# 3. Khởi động backend độc lập và nạp dữ liệu kiểm thử cô lập
./scripts/reset_db.sh

# 4. Thực thi Smoke test kiểm tra 5 endpoints
./scripts/run.sh Load --smoke

# 5. Thực thi các kịch bản kiểm thử tải
./scripts/run.sh Load
./scripts/run.sh Stress
./scripts/run.sh Spike
SOAK_VUS=20 SOAK_SECONDS=600 ./scripts/run.sh Soak

# 6. Tự động phân tích raw logs và tài nguyên
python3 scripts/analyze_raw.py raw_logs/23120367_Stress_raw.csv
python3 scripts/analyze_resources.py evidence/Soak_resources.csv

# 7. Kiểm tra tính toàn vẹn của hồ sơ bài nộp
python3 scripts/check_submission.py
```

---

## 7. Quy cách đóng gói nộp bài

- **Tên file nén:** `23120367_HW05_AI_Performance_100.zip` (trong đó `100` là điểm tự chấm ba chữ số theo quy định).
- **Hạn nộp:** Nộp trực tiếp trên hệ thống Moodle môn học trước thời hạn quy định.
- **Yêu cầu bảo vệ:** Sẵn sàng cho buổi phỏng vấn vấn đáp ngẫu nhiên (Oral Defense 5–7 phút) để giải thích chi tiết về workflow, bằng chứng raw logs, nhận diện sai lệch AI và cấu trúc Agent Skills.
