# Threads Studio

Ứng dụng web tiếng Việt để chuyển văn bản thành giọng đọc ElevenLabs, ghép với video nền và xuất video dọc WebM ngay trong trình duyệt.

## Deploy lên Netlify

1. Trong Netlify, chọn **Add new site → Import an existing project** và kết nối GitHub repository này.
2. Chọn repository `duyqa04122009-debug/main.py`.
3. Đặt **Base directory** là `threads-studio`. Publish directory và Functions directory đã cấu hình trong `netlify.toml`.
4. Trong **Site configuration → Environment variables**, thêm `ELEVENLABS_API_KEY` với API key của bạn.
5. Deploy site.

API key chỉ được sử dụng trong Netlify Function, không đặt trong HTML công khai.

## Cách sử dụng

- Dán nội dung bài Threads vào ô nội dung. Link Threads chưa được tự động trích xuất.
- Chọn voice, tốc độ rồi bấm **Tạo giọng đọc**.
- Chọn video nền và nhạc nền tùy chọn.
- Bấm **Tạo & tải video**. Bản hiện tại xuất WebM, không phải MP4.

## Lưu ý

- Cần API key ElevenLabs và tài khoản có hạn mức sử dụng.
- Danh sách voice ID mẫu có thể cần thay bằng voice ID có trong tài khoản của bạn.
- Phụ đề chia theo thời lượng ước tính, chưa đồng bộ từng từ với giọng đọc.
- Xuất video hoạt động tốt nhất trên Chrome/Edge desktop; một số trình duyệt điện thoại hạn chế MediaRecorder.
