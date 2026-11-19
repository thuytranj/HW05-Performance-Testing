# Đánh giá phản biện quá trình cộng tác cùng AI (AI Critique)

Trong quá trình thực hiện bài kiểm thử hiệu năng, AI hỗ trợ rất tốt việc khởi tạo khung kịch bản k6, tự động xử lý tệp CSV và tính toán các phân vị độ trễ Type-7. Dù vậy, em nhận thấy AI bộc lộ những thiên lệch kỹ thuật và thiếu sót đáng kể nếu không có sự giám sát của con người.

Đầu tiên, AI có xu hướng an toàn quá mức khi ban đầu chỉ đề xuất 40 VUs cho bài Stress và Spike, khiến tải CPU dưới 15% và không thể tìm ra ngưỡng tới hạn của SUT. Thứ hai, AI bỏ qua các bất thường dữ liệu nghiêm trọng: khi endpoint chi tiết sản phẩm trả về giá tiền dạng chuỗi ở ID chẵn (xuất hiện 5,361 lần), AI chỉ âm thầm ép kiểu để script tiếp tục chạy thay vì gắn metric cảnh báo hay tạo issue. Thứ ba, AI đưa ra các kiến nghị tối ưu ngoài phạm vi thực tế như đề xuất dùng Redis hay caching phân tán, trong khi hệ thống chỉ là monolithic Node.js với SQLite 5 sản phẩm; nguyên nhân nghẽn thực sự là tích tụ mảng giỏ hàng trong RAM và thiếu chế độ SQLite WAL. Cuối cùng, việc AI tách đôi lệnh kiểm tra HTTP status đã làm sai lệch tỷ lệ thành công của kịch bản.

Qua đó, bài học lớn nhất là AI chỉ đóng vai trò trợ lý tăng tốc lập trình. Kỹ sư kiểm thử bắt buộc phải trực tiếp thẩm định mã nguồn SUT, kiểm chứng các giả định tải và phân tích dữ liệu tài nguyên thực tế để đảm bảo chất lượng bài đo.
