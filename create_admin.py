#!/usr/bin/env python3
"""
Script để tạo tài khoản admin
Sử dụng: python3 create_admin.py
"""

from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin(username, email, password):
    """Tạo tài khoản admin"""
    with app.app_context():
        # Kiểm tra user đã tồn tại chưa
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"⚠️  Tài khoản '{username}' đã tồn tại.")
            response = input("Bạn có muốn cập nhật thành admin? (y/n): ")
            if response.lower() == 'y':
                existing_user.is_admin = True
                if password:
                    existing_user.password_hash = generate_password_hash(password)
                db.session.commit()
                print(f"✓ Đã cập nhật '{username}' thành admin!")
                return
            else:
                print("Hủy bỏ.")
                return
        
        # Tạo user mới
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True
        )
        db.session.add(user)
        db.session.commit()
        print(f"✓ Đã tạo admin '{username}' thành công!")

if __name__ == '__main__':
    print("=== TẠO TÀI KHOẢN ADMIN ===")
    print()
    username = input("Tên đăng nhập: ").strip()
    email = input("Email: ").strip()
    password = input("Mật khẩu: ").strip()
    
    if not username or not email or not password:
        print("❌ Vui lòng điền đầy đủ thông tin!")
    else:
        create_admin(username, email, password)

