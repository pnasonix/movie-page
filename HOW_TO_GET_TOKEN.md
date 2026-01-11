# Hướng dẫn lấy GitHub Personal Access Token

## Bước 1: Đăng nhập GitHub
Truy cập https://github.com và đăng nhập vào tài khoản của bạn.

## Bước 2: Vào Settings
1. Click vào **avatar/profile picture** ở góc trên bên phải
2. Chọn **Settings** (hoặc truy cập trực tiếp: https://github.com/settings/profile)

## Bước 3: Vào Developer settings
1. Cuộn xuống phần **Developer settings** ở sidebar bên trái
2. Click vào **Developer settings**
3. Hoặc truy cập trực tiếp: https://github.com/settings/apps

## Bước 4: Tạo Personal Access Token
1. Trong **Developer settings**, click vào **Personal access tokens**
2. Chọn **Tokens (classic)** 
3. Hoặc truy cập trực tiếp: https://github.com/settings/tokens
4. Click nút **Generate new token**
5. Chọn **Generate new token (classic)**

## Bước 5: Cấu hình token
1. **Note**: Đặt tên cho token (ví dụ: "gporn-me-push" hoặc "movie-page-deploy")
2. **Expiration**: Chọn thời hạn (30 days, 60 days, 90 days, hoặc No expiration)
3. **Select scopes**: Tích vào ô **repo** (sẽ tự động chọn tất cả quyền repo)
   - ✅ repo (Full control of private repositories)
   - Điều này cho phép đọc, write, và quản lý repositories

## Bước 6: Tạo và copy token
1. Click **Generate token** ở cuối trang
2. **QUAN TRỌNG**: Token chỉ hiển thị 1 lần duy nhất!
3. Copy token ngay lập tức (token có dạng: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`)
4. Lưu token ở nơi an toàn (nếu mất phải tạo lại)

## Bước 7: Sử dụng token để push
```bash
cd /var/www/gporn.me
GITHUB_TOKEN=ghp_your_token_here bash push_with_token.sh
```

## Lưu ý bảo mật
- ⚠️ **KHÔNG** commit token vào git
- ⚠️ **KHÔNG** chia sẻ token công khai
- ⚠️ Token có quyền truy cập đầy đủ vào repositories của bạn
- Nếu token bị lộ, vào Settings → Developer settings → Personal access tokens để **revoke** (thu hồi) ngay

## Link nhanh
- Settings: https://github.com/settings/profile
- Developer settings: https://github.com/settings/apps
- Personal access tokens: https://github.com/settings/tokens
