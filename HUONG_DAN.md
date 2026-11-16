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

Dán vào ô Sub account, mỗi dòng một sub theo dạng `apikey=apisecret` (dòng 1 = Acc1, dòng 2 = Acc2…) → **Lưu cài đặt**. Thẻ Status sẽ hiện số dư từng acc.

> Nên thử trước ở môi trường **Demo Trading** (tạo API key trong chế độ Demo của Bybit) rồi mới chuyển Mainnet.

## 3. Nghe kênh Telegram
Chỉ cần nhập **Channel ID** → **Lưu cài đặt**. Tool không đăng nhập tài khoản Telegram của bạn.

- **Kênh công khai** (có @tenkenh): nhập `@tenkenh`. Tool đọc trang xem trước công khai của kênh, kiểm tra mỗi giây. Có thể trễ vài giây so với lúc tin được đăng.
- **Kênh riêng tư** (chỉ có ID dạng `-100…`): chỉ nghe được khi chủ kênh thêm bot điều khiển của bạn (mục 4) làm admin kênh. Cách này cũng nhanh hơn cho kênh công khai.

## 4. Bot điều khiển từ xa
1. Nhắn @BotFather → `/newbot` → lấy **Bot Token**, dán vào tool → Lưu.
2. Nhắn bất kỳ cho bot của bạn → bot trả về **Chat ID** → dán vào ô "Chat ID chủ bot" → Lưu.
3. Lệnh: `/start` chạy · `/stop` dừng · `/status` xem PnL · `/close` market close tất cả · `/help` xem danh sách lệnh.
4. Mở lệnh tay: `/buy #coin size tp sl` — ví dụ `/buy #eth 1000 10 2` = Long ETHUSDT 1000 USDT, TP +10%, SL −2% so với giá entry. Lệnh này chạy cả khi bot đang dừng.
5. All-in: `/lev 10` đặt đòn bẩy all-in (hoặc `/lev max` = max của coin), rồi `/allin #coin tp sl` — ví dụ `/allin #evaa 10 2`. Mỗi acc mở Long bằng toàn bộ vốn khả dụng × đòn bẩy. Coin chỉ cho đòn bẩy thấp hơn (vd EVAA x4) thì tool tự hạ xuống max của coin. Tool chừa khoảng 3% vốn + phí để lệnh không bị từ chối.

Bot cũng tự báo về Telegram mỗi khi tool vào lệnh.

## 5. Nút Update New Ver
Link update đã gắn sẵn vào repo https://github.com/meohocgioi/BabyBB — không cần dán gì.
Mỗi khi có bản mới được đẩy lên repo, bấm **Update New Ver** → tool tự tải, kiểm tra và khởi động lại. Cài đặt của bạn giữ nguyên.

Cập nhật từ xa: gõ `/update` cho bot Telegram. Tool tải bản mới, chạy thử, thay file, khởi động lại, rồi bot gửi change log. Bản mới lỗi khi khởi động thì tool tự quay về bản cũ. Tool **không** tự cập nhật khi bạn chưa ra lệnh.

API key **không** nằm trong `bybit_copy.py` mà nằm trong `config.json` trên máy bạn — đừng bao giờ upload `config.json` lên GitHub.

## 6. Cách tool vào lệnh
- Lệnh: `m #coin size tp sl` — ví dụ `m #space 1 10 2` = Long SPACEUSDT, position 1000 USDT, TP +10%, SL −2%.
- Nếu đã đặt `/lev N`: mọi lệnh dùng đòn bẩy đó (size không đổi, chỉ ký quỹ giảm); size cần cao hơn thì tool tự nâng.
- Nếu chưa đặt `/lev`: đòn bẩy tự tính = nhỏ nhất đủ mở position với số dư khả dụng (trừ hao 5% cho phí). Số dư 100 USDT, size 1000 → x11.
- Nếu vượt max đòn bẩy của coin, tool tự giảm size xuống mức tối đa mở được và ghi rõ trong log.
- Tốc độ: giá và số dư được cập nhật sẵn ở nền, đòn bẩy được đặt song song với lệnh, nên mỗi acc chỉ cần một lượt gửi tới Bybit. Con số "ms" trong tin báo là thời gian từ lúc tool nhận lệnh tới lúc cả 5 acc được Bybit xác nhận.
- TP/SL gắn ngay vào lệnh market, sau khi khớp được chỉnh lại theo đúng giá entry thực tế.
- Tool chỉ vào lệnh khi đang **ĐANG CHẠY**; tin cũ hơn 60 giây bị bỏ qua.
