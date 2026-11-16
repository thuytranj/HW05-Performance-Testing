# Hướng dẫn agent — HW05 Performance Testing

## Phạm vi và tài liệu cần đọc

Repository chứa SUT EShop và bài HW05 cá nhân dùng k6. Giao tiếp với người dùng bằng tiếng Việt; giữ tên API, metric và file nhất quán với source.

- Đọc `docs/architecture.md` để hiểu cấu trúc project và workspace bài tập.
- Khi thiết kế, chạy, review hoặc viết báo cáo performance, dùng `.agents/skills/eshop-k6-performance/SKILL.md` và checklist tham chiếu của skill.
- Đề gốc là `docs/2026.HW05.Performance Testing_En.pdf`. Nếu checklist khác đề, đối chiếu đề và báo rõ khác biệt.
- Xác minh API bằng `backend/server.js`, `backend/database.js`, cấu hình triển khai và `api_specification.md`; không mặc định tài liệu API luôn khớp implementation.

Làm đầy đủ công việc đã được người dùng giao. Tạo tài liệu hoặc plan không đồng nghĩa đã được giao chạy tải. Khi người dùng đã giao chạy, tiếp tục các bước chuẩn bị/kiểm chứng cần thiết trong phạm vi đó, không hỏi lại việc đã được cho phép. Chỉ commit, push, đăng issue, upload video hoặc nộp bài khi có chỉ dẫn tương ứng.

## Quy ước bài tập

- Mặc định StudentID `23120367`; cho phép đổi qua cấu hình. Ngày plan là ngày chạy thật `YYYYMMDD`, múi giờ `Asia/Ho_Chi_Minh`.
- Cả Load, Stress và Spike dùng cùng flow: login → search → product detail → add cart → checkout. Bao phủ auth-heavy, read-heavy, transactional; sinh viên xác nhận không trùng workflow với thành viên nhóm.
- Dùng workflow chung, `SharedArray`, CSV ít nhất 40 dòng hợp lệ và một tài khoản độc lập/VU. Số account phải đủ peak VUs; không modulo để dùng chung tài khoản.
- Giữ naming `<StudentID>_<Load|Stress|Spike>_<YYYYMMDD>.js`; Soak là plan bổ sung, giữ tải 10–15 phút.
- Ba view riêng: Load built-in dashboard, Stress k6-reporter tabbed HTML, Spike custom group/status HTML. Giữ đúng tên/path đã định trong skill.
- Think-time, tải và thresholds là giả định cần giải thích và đo thực nghiệm; không trình bày giá trị mặc định thành kết quả hoặc ngưỡng phần cứng đã xác nhận.

## Bảo vệ SUT và dữ liệu

- Backend gốc có destructive seed khi import `database.js`. Không chạy seed/restart gốc để reset bài performance; dùng runtime cô lập của skill.
- Không dùng `run_servers.sh` để đo tải vì script gọi `killall node`. Chỉ quản lý PID runtime thuộc workspace hiện tại.
- Không reset/stop backend trong lúc đo. Không thay đổi source SUT hoặc sửa lỗi nghiệp vụ chỉ để làm kết quả test đạt.
- Login hiện tăng attempts thêm 2, khóa khi >=3 trong 180000ms. Ghi đúng implementation; không khẳng định lỗi đã tái hiện nếu mới đọc source.
- Cart ở RAM và checkout không xóa cart. Products hiện không có cột tồn kho; không bịa SQL stock/reset hay kết luận thiếu tồn kho.
- Giữ `.env` và dữ liệu thật ngoài hồ sơ public. CSV của bài dùng tài khoản fixture tổng hợp trong DB kiểm thử.

## Tổ chức thay đổi và bằng chứng

- SUT ở `backend/`, `frontend-*`; tài liệu project ở `docs/`; skill gốc ở `.agents/skills/`; workspace bài mặc định ở `performance/`.
- Sinh workspace bằng bootstrap; không tạo trước các file raw logs, ảnh, PDF hoặc kết quả rỗng để đánh dấu hoàn tất.
- Bootstrap chỉ dùng output trống. Khi chạy lại, chọn workspace mới và giữ nguyên bằng chứng cũ. Không ghi đè kết quả fail.
- Đổi source SUT phải discovery lại và tạo workspace mới. Phân biệt chỉnh asset của skill với chỉnh plans của một lần đo; hai nơi không tự đồng bộ.
- Giữ nguyên các thay đổi có sẵn của người dùng. Khi được giao commit, chia theo bước có ý nghĩa và xuất Git commit log dạng text cho bài nộp.
- Không tạo subagent trừ khi người dùng hoặc một skill đang áp dụng yêu cầu delegation cụ thể.

## Kiểm chứng

Smoke thực thi trước tải lớn: 1 VU, 1 iteration. Kiểm tra token, HTTP 200/201, body, product ID và orderId; `k6 inspect` không thay thế smoke. HTTP 200 một mình chưa chứng minh nghiệp vụ thành công.

Với mỗi full scenario, giữ raw CSV, JSON summary, HTML, run manifest và resource samples của backend. Exit99 là threshold breach, không gọi là pass. Smoke output không thay bằng chứng full Load/Stress/Spike/Soak. Sub-second smoke có thể không sinh dashboard HTML.

Phân tích từ raw samples: latency ms, error rate 0..1, percentile Type-7; dùng cửa sổ chung cho RPS. Tách HTTP requests/s với completed checkout/s, HTTP failure với business/flow failure. Không lấy trung bình p95 của endpoint; không suy raw samples từ summary JSON. Dùng window plateau/recovery/soak khi đánh giá ổn định. Không gọi một mức tải pass đơn lẻ là trần tối đa.

Khi sửa helpers, chạy từ project root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s .agents/skills/eshop-k6-performance/tests -v
```

Chạy thêm smoke trên backend cô lập khi thay workflow, parser, reporter hoặc runtime; nêu rõ giới hạn kiểm chứng. Chỉ sửa Markdown thì kiểm tra nội dung, link và tên/path liên quan; không cần chạy tải. `backend/package.json` hiện chưa có test suite hoạt động, nên không báo `npm test` backend là đã pass.

## AI Audit, review và hồ sơ nộp

- AI Audit chỉ dùng `audit/ai-audit.md` và bản PDF khi nộp. Mỗi lượt hỏi–đáp ghi tool/model, thời gian thật có timezone, prompt và final response hiển thị cho người dùng; không ghi suy nghĩ nội bộ, reasoning, commentary/progress hay tool-call traces. Không tạo `interactions/` hoặc `interactions.jsonl` mới. Không tái dựng lịch sử còn thiếu, bỏ final response của các lượt trước hay xóa human review đã có. Raw logs test vẫn giữ riêng đầy đủ.
- Giữ phân tích AI đầu tiên trước khi sửa. Bảng kiểm chứng dẫn raw filename/hash, metric, scope, số mẫu và giá trị đúng; không bịa nhận định sai của AI.
- Đánh giá tối ưu bằng SQLite schema/code/query plan hoặc thực nghiệm, không dùng lời khuyên kiến trúc DB chưa xác minh.
- Human review và AI Critique một đoạn 200–300 từ phải phản ánh đánh giá thực tế của sinh viên; không viết thay để giả thành suy nghĩ cá nhân.
- Nhắc ảnh tool + backend monitor cùng khung hình, cấu hình máy/hostname thật, video unlisted tổng >=6 phút và giọng Việt của sinh viên. `Thuys-MacBook-Air` là hostname dự kiến do người dùng cung cấp; luôn xác minh hostname thật và khớp bài trước.
- Cần main report, AI Audit, AI Critique ở Markdown+PDF; kiểm tra bản render PDF. Có flowchart continuous testing, p95 baseline/regression, chi phí và false alarms; README tự chấm và tổng kết; skill cùng demo sử dụng.
- Đề cho k6 nhưng liệt kê `.jtl`: giữ native CSV, ghi nhận chỗ chưa thống nhất và xác nhận TA; không đổi đuôi để giả JMeter log.
- Dùng `check_submission.py` để kiểm tra file/cấu trúc rồi review thủ công. Không tự điền điểm, bằng chứng, kết quả hoặc trạng thái đã nộp. Báo rõ việc nào hoàn tất và việc nào còn cần sinh viên thực hiện.
