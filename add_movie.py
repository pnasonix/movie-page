#!/usr/bin/env python3
"""
Script để thêm phim mới vào database
Sử dụng: python3 add_movie.py
"""

import sys
from app import app, db, Movie, Category

def add_movie(title, description, video_url, poster_url, category_name=None):
    """Thêm một phim mới vào database"""
    with app.app_context():
        # Tìm category nếu có
        category_id = None
        if category_name:
            category = Category.query.filter_by(name=category_name).first()
            if category:
                category_id = category.id
            else:
                print(f"⚠️  Thể loại '{category_name}' không tồn tại. Tạo phim không có thể loại.")
        
        # Tạo phim mới
        movie = Movie(
            title=title,
            description=description,
            video_url=video_url,
            poster_url=poster_url,
            category_id=category_id
        )
        
        db.session.add(movie)
        db.session.commit()
        print(f"✓ Đã thêm phim: {title} (ID: {movie.id})")
        return movie

def list_categories():
    """Liệt kê tất cả thể loại"""
    with app.app_context():
        categories = Category.query.all()
        print("\nDanh sách thể loại:")
        for cat in categories:
            print(f"  - {cat.name}")
        return categories

def list_movies():
    """Liệt kê tất cả phim"""
    with app.app_context():
        movies = Movie.query.all()
        print(f"\nTổng số phim: {len(movies)}")
        for movie in movies:
            print(f"  [{movie.id}] {movie.title} - {movie.category.name if movie.category else 'Không có thể loại'}")
        return movies

if __name__ == '__main__':
    with app.app_context():
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == 'list':
                list_movies()
            elif command == 'categories':
                list_categories()
            elif command == 'add':
                if len(sys.argv) < 4:
                    print("Sử dụng: python3 add_movie.py add <title> <video_url> [poster_url] [category]")
                    print("Ví dụ: python3 add_movie.py add 'Phim Mới' 'https://example.com/video.mp4' 'https://example.com/poster.jpg' 'Hành động'")
                    sys.exit(1)
                
                title = sys.argv[2]
                video_url = sys.argv[3]
                poster_url = sys.argv[4] if len(sys.argv) > 4 else 'https://via.placeholder.com/300x450?text=' + title.replace(' ', '+')
                category = sys.argv[5] if len(sys.argv) > 5 else None
                description = input("Nhập mô tả phim (Enter để bỏ qua): ").strip() or None
                
                add_movie(title, description, video_url, poster_url, category)
            else:
                print("Lệnh không hợp lệ. Sử dụng: list, categories, hoặc add")
        else:
            print("=== QUẢN LÝ PHIM ===")
            print("\nCác lệnh:")
            print("  python3 add_movie.py list          - Liệt kê tất cả phim")
            print("  python3 add_movie.py categories     - Liệt kê thể loại")
            print("  python3 add_movie.py add <args>     - Thêm phim mới")
            print("\nVí dụ thêm phim:")
            print("  python3 add_movie.py add 'Tên Phim' 'https://video-url.mp4' 'https://poster.jpg' 'Hành động'")

