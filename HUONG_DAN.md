# Bybit Multi-Sub Copy — Hướng dẫn cài đặt

## 1. Chạy tool
Chỉ cần **một file**: `BabyBB.bat`. Tải về, để ở Desktop, bấm đúp để chạy.
- Lần đầu file tự tải tool, tự cài thư viện (và thử tự cài Python nếu máy chưa có).
- Trình duyệt tự mở http://127.0.0.1:8787. Giữ cửa sổ đen mở trong lúc dùng; đóng cửa sổ đen = tắt tool.
- Mọi thứ khác (code, cài đặt, API key) nằm trong thư mục `C:\Users\<tên bạn>\BabyBB` — bạn không cần đụng vào.

## 2. Sub account Bybit
Với **từng** sub account: đăng nhập sub → API Management → tạo API key
- Quyền: chỉ **Contract – Orders + Positions** (Read-Write). **Không** bật Withdraw/Transfer.
- Nên khoá IP theo IP nhà bạn.
- Sub account phải là **Unified Trading Account**, position mode **One-Way**.

Dán Tên / API Key / API Secret vào tool → **Lưu cài đặt**. Thẻ Status sẽ hiện số dư từng acc.

> Nên thử trước ở môi trường **Demo Trading** (tạo API key trong chế độ Demo của Bybit) rồi mới chuyển Mainnet.

## 3. Nghe kênh Telegram (kênh của người khác)
1. Vào https://my.telegram.org → API development tools → tạo app → lấy **API ID** và **API Hash**.
2. Nhập API ID, API Hash, số điện thoại (+84…) → **Lưu & gửi mã**.
3. Nhập mã Telegram gửi về (và mật khẩu 2 lớp nếu có) → **Đăng nhập**.
4. **Tải danh sách** → chọn kênh phát lệnh → **Lưu cài đặt**.

## 4. Bot điều khiển từ xa
1. Nhắn @BotFather → `/newbot` → lấy **Bot Token**, dán vào tool → Lưu.
2. Nhắn bất kỳ cho bot của bạn → bot trả về **Chat ID** → dán vào ô "Chat ID chủ bot" → Lưu.
3. Lệnh: `/start` chạy · `/stop` dừng · `/close` market close tất cả · `/status` xem PnL.

Bot cũng tự báo về Telegram mỗi khi tool vào lệnh.

## 5. Nút Update New Ver
Link update đã gắn sẵn vào repo https://github.com/meohocgioi/BabyBB — không cần dán gì.
Mỗi khi có bản mới được đẩy lên repo, bấm **Update New Ver** → tool tự tải, kiểm tra và khởi động lại. Cài đặt của bạn giữ nguyên.

API key **không** nằm trong `bybit_copy.py` mà nằm trong `config.json` trên máy bạn — đừng bao giờ upload `config.json` hay `tg_session.session` lên GitHub.

## 6. Cách tool vào lệnh
- Lệnh: `m #coin size tp sl` — ví dụ `m #space 1 10 2` = Long SPACEUSDT, position 1000 USDT, TP +10%, SL −2%.
- Đòn bẩy tự tính = nhỏ nhất đủ mở position với số dư khả dụng (trừ hao 5% cho phí). Số dư 100 USDT, size 1000 → x11.
- Nếu vượt max đòn bẩy của coin, tool tự giảm size xuống mức tối đa mở được và ghi rõ trong log.
- TP/SL gắn ngay vào lệnh market, sau khi khớp được chỉnh lại theo đúng giá entry thực tế.
- Tool chỉ vào lệnh khi đang **ĐANG CHẠY**; tin cũ hơn 60 giây bị bỏ qua.
