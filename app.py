from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from sqlalchemy import text
import logging
from logging.handlers import RotatingFileHandler
import os
import uuid
import re
import unicodedata

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///movies.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['CSS_VERSION'] = os.environ.get('CSS_VERSION', '9.0')
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'movies'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'posters'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)

try:
    os.makedirs(app.instance_path, exist_ok=True)
    log_file = os.path.join(app.instance_path, 'app.log')
    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
    file_handler.setFormatter(formatter)
    if not app.logger.handlers:
        app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application logging initialized')
except Exception as e:
    print(f"Could not set up logging: {e}")

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    avatar_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    watch_history = db.relationship('WatchHistory', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    movies = db.relationship('Movie', backref='category', lazy=True)

class Franchise(db.Model):
    """Nhóm các phim cùng series (VD: Maze Runner 1, 2, 3)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    poster_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    movies = db.relationship('Movie', backref='franchise', lazy=True, order_by='Movie.created_at')

def slugify(text):
    """Tạo slug từ tiếng Việt"""
    # Bảng chuyển đổi tiếng Việt
    vietnamese_map = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    }
    text = text.lower()
    for vn_char, ascii_char in vietnamese_map.items():
        text = text.replace(vn_char, ascii_char)
    # Loại bỏ ký tự đặc biệt, giữ lại chữ và số
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    # Thay khoảng trắng bằng dấu gạch ngang
    text = re.sub(r'[\s_]+', '-', text)
    # Loại bỏ dấu gạch ngang thừa
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(200), nullable=True)  # Tiêu đề phụ (thường là tên tiếng Anh)
    slug = db.Column(db.String(250), unique=True, nullable=True)  # Deprecated, kept for backward compatibility
    url_key = db.Column(db.String(12), unique=True, nullable=True)  # Random key for URL
    description = db.Column(db.Text)
    video_url = db.Column(db.String(500))
    poster_url = db.Column(db.String(500))
    subtitle_url = db.Column(db.String(500))  # URL file phụ đề (.vtt, .srt)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    display_order = db.Column(db.Integer, default=0)  # Thứ tự hiển thị trên trang chủ
    # Franchise support (movie series like Maze Runner 1, 2, 3)
    franchise_id = db.Column(db.Integer, db.ForeignKey('franchise.id'), nullable=True)
    # Episodes support (TV show episodes)
    series_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=True)  # Parent series ID (null if standalone or is series itself)
    episode_number = db.Column(db.Integer, nullable=True)  # Episode number (null if standalone movie)
    is_series = db.Column(db.Boolean, default=False)  # True if this is a series container (phim bộ)
    watch_history = db.relationship('WatchHistory', backref='movie', lazy=True)
    episodes = db.relationship('Movie', backref=db.backref('series', remote_side=[id]), lazy=True, foreign_keys=[series_id])
    
    def generate_slug(self):
        """Tạo slug từ title - deprecated"""
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        while Movie.query.filter(Movie.slug == slug, Movie.id != self.id).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug
        return slug
    
    def generate_url_key(self):
        """Tạo url_key ngẫu nhiên dựa trên timestamp và random"""
        import time
        import random
        import string
        # Kết hợp timestamp (base36) + random chars để tạo key ngắn gọn
        timestamp_part = hex(int(time.time()))[2:][-4:]  # 4 ký tự cuối của hex timestamp
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        url_key = f"{timestamp_part}{random_part}"
        # Đảm bảo unique
        while Movie.query.filter(Movie.url_key == url_key, Movie.id != self.id).first():
            random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            url_key = f"{timestamp_part}{random_part}"
        self.url_key = url_key
        return url_key

class WatchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_position = db.Column(db.Integer, default=0)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)  # For replies
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)

class CommentLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='unique_comment_like'),)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_categories():
    try:
        categories = Category.query.order_by(Category.name.asc()).all()
    except Exception:
        db.session.rollback()
        categories = []
    return dict(categories=categories)

@app.context_processor
def inject_static_versions():
    def get_file_version(filename):
        file_path = os.path.join(app.static_folder, filename)
        try:
            mtime = os.path.getmtime(file_path)
            return str(int(mtime))
        except:
            return app.config['CSS_VERSION']
    return dict(
        css_version=get_file_version('css/style.css'),
        js_version=get_file_version('js/main.js')
    )

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bạn không có quyền truy cập trang này.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    try:
        categories = Category.query.all()
    except Exception:
        db.session.rollback()
        categories = []
    
    filter_type = request.args.get('filter', 'all')
    try:
        if filter_type == 'popular':
            movies = Movie.query.order_by(Movie.views.desc()).all()
        elif filter_type == 'newest':
            movies = Movie.query.order_by(Movie.created_at.desc()).all()
        elif filter_type == 'watched' and current_user.is_authenticated:
            history_rows = db.session.query(WatchHistory, Movie).join(
                Movie, WatchHistory.movie_id == Movie.id
            ).filter(
                WatchHistory.user_id == current_user.id
            ).order_by(WatchHistory.watched_at.desc()).limit(100).all()
            seen = set()
            ordered_movies = []
            for _, movie in history_rows:
                if movie.id not in seen:
                    seen.add(movie.id)
                    ordered_movies.append(movie)
            movies = ordered_movies
        elif filter_type == 'liked' and current_user.is_authenticated:
            fav_rows = db.session.query(Favorite, Movie).join(
                Movie, Favorite.movie_id == Movie.id
            ).filter(
                Favorite.user_id == current_user.id
            ).order_by(Favorite.created_at.desc()).limit(100).all()
            movies = [movie for _, movie in fav_rows]
        else:
            movies = Movie.query.order_by(Movie.display_order.asc(), Movie.created_at.desc()).all()
    except Exception:
        db.session.rollback()
        movies = []
    
    return render_template('index.html', movies=movies, categories=categories, filter_type=filter_type)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not username or not email or not password:
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Tên người dùng đã tồn tại.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng.', 'error')
            return render_template('register.html')
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Có lỗi xảy ra. Vui lòng thử lại.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/movie/<url_key>')
def movie(url_key):
    # Thử tìm theo url_key trước
    movie_obj = Movie.query.filter_by(url_key=url_key).first()
    
    # Nếu không tìm thấy theo url_key, thử tìm theo slug (backward compatibility)
    if not movie_obj:
        movie_obj = Movie.query.filter_by(slug=url_key).first()
        # Nếu tìm thấy theo slug và có url_key, redirect sang URL mới
        if movie_obj and movie_obj.url_key:
            return redirect(url_for('movie', url_key=movie_obj.url_key), code=301)
    
    # Nếu vẫn không tìm thấy, thử tìm theo id
    if not movie_obj and url_key.isdigit():
        movie_obj = Movie.query.get(int(url_key))
        # Nếu tìm thấy theo id và có url_key, redirect sang URL mới
        if movie_obj and movie_obj.url_key:
            return redirect(url_for('movie', url_key=movie_obj.url_key), code=301)
    
    if not movie_obj:
        from flask import abort
        abort(404)
    
    try:
        movie_obj.views += 1
        db.session.commit()
    except:
        db.session.rollback()
    
    if current_user.is_authenticated:
        try:
            existing = WatchHistory.query.filter_by(
                user_id=current_user.id,
                movie_id=movie_obj.id
            ).first()
            
            if existing:
                existing.watched_at = datetime.utcnow()
            else:
                history = WatchHistory(user_id=current_user.id, movie_id=movie_obj.id)
                db.session.add(history)
            
            db.session.commit()
        except:
            db.session.rollback()
    
    is_favorited = False
    if current_user.is_authenticated:
        is_favorited = Favorite.query.filter_by(
            user_id=current_user.id,
            movie_id=movie_obj.id
        ).first() is not None
    
    # Lấy phim cùng thể loại (Có thể bạn sẽ thích)
    suggested_movies = []
    if movie_obj.category_id:
        query = Movie.query.filter(
            Movie.category_id == movie_obj.category_id,
            Movie.id != movie_obj.id,
            Movie.series_id == None  # Chỉ lấy phim độc lập hoặc series, không lấy episodes
        )
        # Nếu phim thuộc franchise, loại trừ các phim cùng franchise
        if movie_obj.franchise_id:
            query = query.filter(
                db.or_(Movie.franchise_id == None, Movie.franchise_id != movie_obj.franchise_id)
            )
        suggested_movies = query.order_by(Movie.views.desc()).limit(10).all()
    
    # Lấy các phần trong cùng franchise (series phim như Maze Runner 1, 2, 3)
    franchise_movies = []
    current_franchise = None
    if movie_obj.franchise_id:
        current_franchise = movie_obj.franchise
        franchise_movies = Movie.query.filter(
            Movie.franchise_id == movie_obj.franchise_id,
            Movie.id != movie_obj.id
        ).order_by(Movie.created_at.asc()).all()
    
    # Lấy danh sách tập nếu là phim bộ (dài tập)
    episodes = []
    current_series = None
    
    if movie_obj.is_series:
        # Nếu đây là series (phim bộ), lấy tất cả các tập
        current_series = movie_obj
        episodes = Movie.query.filter(
            Movie.series_id == movie_obj.id
        ).order_by(Movie.episode_number.asc()).all()
    elif movie_obj.series_id:
        # Nếu đây là một tập, lấy series và tất cả các tập khác
        current_series = Movie.query.get(movie_obj.series_id)
        if current_series:
            episodes = Movie.query.filter(
                Movie.series_id == current_series.id
            ).order_by(Movie.episode_number.asc()).all()
    
    # Lấy bình luận cho phim
    comments = Comment.query.filter_by(movie_id=movie_obj.id, parent_id=None).order_by(Comment.created_at.desc()).all()
    return render_template('movie.html', 
                         movie=movie_obj, 
                         is_favorite=is_favorited, 
                         suggested_movies=suggested_movies,
                         franchise_movies=franchise_movies,
                         current_franchise=current_franchise,
                         episodes=episodes,
                         current_series=current_series,
                         comments=comments)

@app.route('/category/<int:category_id>')
def category(category_id):
    category = Category.query.get_or_404(category_id)
    movies = Movie.query.filter_by(category_id=category_id).order_by(Movie.created_at.desc()).all()
    return render_template('category.html', category=category, movies=movies)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        movies = Movie.query.filter(
            db.or_(
                Movie.title.ilike(f'%{query}%'),
                Movie.subtitle.ilike(f'%{query}%')
            )
        ).all()
    else:
        movies = []
    return render_template('search.html', movies=movies, query=query)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    movies = Movie.query.filter(
        db.or_(
            Movie.title.ilike(f'%{query}%'),
            Movie.subtitle.ilike(f'%{query}%')
        )
    ).limit(10).all()
    results = []
    for movie in movies:
        results.append({
            'id': movie.id,
            'url_key': movie.url_key or movie.slug or str(movie.id),
            'title': movie.title,
            'subtitle': movie.subtitle or '',
            'poster_url': movie.poster_url or '',
            'category': movie.category.name if movie.category else '',
            'views': movie.views
        })
    return jsonify(results)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    
    if not username or not email:
        flash('Vui lòng điền đầy đủ thông tin.', 'error')
        return redirect(url_for('profile'))
    
    # Kiểm tra username đã tồn tại (trừ chính user hiện tại)
    existing_user = User.query.filter(User.username == username, User.id != current_user.id).first()
    if existing_user:
        flash('Tên người dùng đã được sử dụng.', 'error')
        return redirect(url_for('profile'))
    
    # Kiểm tra email đã tồn tại (trừ chính user hiện tại)
    existing_email = User.query.filter(User.email == email, User.id != current_user.id).first()
    if existing_email:
        flash('Email đã được sử dụng.', 'error')
        return redirect(url_for('profile'))
    
    try:
        current_user.username = username
        current_user.email = email
        db.session.commit()
        flash('Cập nhật thông tin thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi cập nhật.', 'error')
    
    return redirect(url_for('profile'))

@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar_file' not in request.files:
        flash('Không có file nào được chọn.', 'error')
        return redirect(url_for('profile'))
    
    file = request.files['avatar_file']
    if file.filename == '':
        flash('Không có file nào được chọn.', 'error')
        return redirect(url_for('profile'))
    
    if file:
        filename = secure_filename(file.filename)
        # Tạo tên file unique
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
        new_filename = f"{uuid.uuid4().hex}.{ext}"
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars', new_filename)
        try:
            file.save(filepath)
            avatar_url = url_for('static', filename=f'uploads/avatars/{new_filename}')
            current_user.avatar_url = avatar_url
            db.session.commit()
            flash('Cập nhật ảnh đại diện thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Có lỗi xảy ra khi tải lên ảnh.', 'error')
    
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        flash('Vui lòng điền đầy đủ thông tin.', 'error')
        return redirect(url_for('profile'))
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Mật khẩu hiện tại không đúng.', 'error')
        return redirect(url_for('profile'))
    
    if new_password != confirm_password:
        flash('Mật khẩu mới không khớp.', 'error')
        return redirect(url_for('profile'))
    
    try:
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash('Đổi mật khẩu thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi đổi mật khẩu.', 'error')
    
    return redirect(url_for('profile'))

@app.route('/favorites')
@login_required
def favorites():
    fav_movies = db.session.query(Movie).join(Favorite).filter(
        Favorite.user_id == current_user.id
    ).order_by(Favorite.created_at.desc()).all()
    return render_template('favorites.html', movies=fav_movies)

@app.route('/api/favorite/<int:movie_id>', methods=['POST'])
@login_required
def toggle_favorite(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    
    try:
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({'success': True, 'is_favorite': False, 'status': 'removed'})
        else:
            new_favorite = Favorite(user_id=current_user.id, movie_id=movie_id)
            db.session.add(new_favorite)
            db.session.commit()
            return jsonify({'success': True, 'is_favorite': True, 'status': 'added'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/watch-history/<int:movie_id>', methods=['POST'])
@login_required
def update_watch_history(movie_id):
    data = request.get_json()
    position = data.get('position', 0)
    
    try:
        history = WatchHistory.query.filter_by(
            user_id=current_user.id,
            movie_id=movie_id
        ).first()
        
        if history:
            history.last_position = position
            history.watched_at = datetime.utcnow()
        else:
            history = WatchHistory(
                user_id=current_user.id,
                movie_id=movie_id,
                last_position=position
            )
            db.session.add(history)
        
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Comments API
@app.route('/comments', methods=['GET', 'POST'])
def comments():
    movie_id = request.args.get('movie_id', type=int)
    
    if request.method == 'GET':
        if not movie_id:
            return jsonify({'comments': [], 'count': 0})
        
        # Get top-level comments only (parent_id is None)
        comments_list = Comment.query.filter_by(movie_id=movie_id, parent_id=None)\
            .order_by(Comment.created_at.desc()).all()
        
        def serialize_comment(c):
            # Count likes
            likes_count = CommentLike.query.filter_by(comment_id=c.id).count()
            # Check if current user liked
            user_liked = False
            if current_user.is_authenticated:
                user_liked = CommentLike.query.filter_by(
                    user_id=current_user.id, comment_id=c.id
                ).first() is not None
            
            # Get replies
            replies_data = []
            for reply in sorted(c.replies, key=lambda r: r.created_at):
                reply_likes = CommentLike.query.filter_by(comment_id=reply.id).count()
                reply_user_liked = False
                if current_user.is_authenticated:
                    reply_user_liked = CommentLike.query.filter_by(
                        user_id=current_user.id, comment_id=reply.id
                    ).first() is not None
                replies_data.append({
                    'id': reply.id,
                    'content': reply.content,
                    'created_at': reply.created_at.isoformat(),
                    'likes_count': reply_likes,
                    'user_liked': reply_user_liked,
                    'user': {
                        'id': reply.user.id if reply.user else None,
                        'username': reply.user.username if reply.user else 'Người dùng',
                        'avatar_url': reply.user.avatar_url if reply.user and hasattr(reply.user, 'avatar_url') else None
                    }
                })
            
            return {
                'id': c.id,
                'content': c.content,
                'created_at': c.created_at.isoformat(),
                'likes_count': likes_count,
                'user_liked': user_liked,
                'replies': replies_data,
                'user': {
                    'id': c.user.id if c.user else None,
                    'username': c.user.username if c.user else 'Người dùng',
                    'avatar_url': c.user.avatar_url if c.user and hasattr(c.user, 'avatar_url') else None
                }
            }
        
        result = [serialize_comment(c) for c in comments_list]
        total_count = len(result) + sum(len(c['replies']) for c in result)
        
        return jsonify({'comments': result, 'count': total_count})
    
    elif request.method == 'POST':
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Vui lòng đăng nhập để bình luận'}), 401
        
        data = request.get_json()
        movie_id = data.get('movie_id')
        content = data.get('content', '').strip()
        parent_id = data.get('parent_id')  # For replies
        
        if not movie_id or not content:
            return jsonify({'success': False, 'error': 'Thiếu thông tin'}), 400
        
        try:
            comment = Comment(
                user_id=current_user.id,
                movie_id=movie_id,
                content=content,
                parent_id=parent_id if parent_id else None
            )
            db.session.add(comment)
            db.session.commit()
            return jsonify({'success': True, 'comment_id': comment.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/comments/<int:comment_id>/like', methods=['POST'])
@login_required
def toggle_comment_like(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    existing_like = CommentLike.query.filter_by(
        user_id=current_user.id, comment_id=comment_id
    ).first()
    
    try:
        if existing_like:
            db.session.delete(existing_like)
            db.session.commit()
            likes_count = CommentLike.query.filter_by(comment_id=comment_id).count()
            return jsonify({'success': True, 'liked': False, 'likes_count': likes_count})
        else:
            new_like = CommentLike(user_id=current_user.id, comment_id=comment_id)
            db.session.add(new_like)
            db.session.commit()
            likes_count = CommentLike.query.filter_by(comment_id=comment_id).count()
            return jsonify({'success': True, 'liked': True, 'likes_count': likes_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    # Chỉ admin hoặc chủ comment mới được xóa
    if not current_user.is_admin and comment.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Không có quyền'}), 403
    
    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_movies = Movie.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()
    total_franchises = Franchise.query.count()
    total_views = db.session.query(db.func.sum(Movie.views)).scalar() or 0
    recent_movies = Movie.query.order_by(Movie.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', 
                         total_movies=total_movies,
                         total_users=total_users,
                         total_categories=total_categories,
                         total_franchises=total_franchises,
                         total_views=total_views,
                         recent_movies=recent_movies)

@app.route('/admin/movies')
@login_required
@admin_required
def admin_movies():
    movies = Movie.query.order_by(Movie.display_order.asc(), Movie.created_at.desc()).all()
    categories = Category.query.all()
    return render_template('admin/movies.html', movies=movies, categories=categories)

@app.route('/admin/movies/reorder', methods=['POST'])
@login_required
@admin_required
def admin_reorder_movies():
    """API endpoint để lưu thứ tự phim sau khi kéo thả"""
    try:
        data = request.get_json()
        movie_ids = data.get('movie_ids', [])
        
        for index, movie_id in enumerate(movie_ids):
            movie = Movie.query.get(movie_id)
            if movie:
                movie.display_order = index
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/movies/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_movie():
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')  # Tiêu đề phụ (tiếng Anh)
        description = request.form.get('description')
        video_url = request.form.get('video_url')
        poster_url = request.form.get('poster_url')
        subtitle_url = request.form.get('subtitle_url')
        category_id = request.form.get('category_id')
        
        # Franchise (series phim) field
        franchise_id = request.form.get('franchise_id')
        
        # Episodes (phim bộ) fields
        is_series = request.form.get('is_series') == '1'
        series_id = request.form.get('series_id')
        episode_number = request.form.get('episode_number')
        
        # Handle subtitle file upload
        subtitle_file = request.files.get('subtitle')
        if subtitle_file and subtitle_file.filename:
            from werkzeug.utils import secure_filename
            import uuid
            filename = secure_filename(subtitle_file.filename)
            # Add unique prefix to avoid conflicts
            unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
            subtitle_path = os.path.join(app.static_folder, 'uploads', 'subtitles', unique_filename)
            subtitle_file.save(subtitle_path)
            subtitle_url = url_for('static', filename=f'uploads/subtitles/{unique_filename}')
        
        if not title:
            flash('Vui lòng nhập tên phim.', 'error')
            return redirect(url_for('admin_add_movie'))
        
        new_movie = Movie(
            title=title,
            subtitle=subtitle,
            description=description,
            video_url=video_url,
            poster_url=poster_url,
            subtitle_url=subtitle_url,
            category_id=category_id if category_id else None,
            franchise_id=int(franchise_id) if franchise_id else None,
            is_series=is_series,
            series_id=int(series_id) if series_id and not is_series else None,
            episode_number=int(episode_number) if episode_number and not is_series else None
        )
        
        try:
            db.session.add(new_movie)
            db.session.flush()  # Để có ID trước khi tạo url_key
            new_movie.generate_url_key()
            new_movie.generate_slug()  # Giữ slug cho SEO
            db.session.commit()
            flash('Thêm phim thành công!', 'success')
            return redirect(url_for('admin_movies'))
        except Exception as e:
            db.session.rollback()
            flash('Có lỗi xảy ra.', 'error')
    
    categories = Category.query.all()
    # Lấy danh sách các series (phim bộ)
    all_series = Movie.query.filter_by(is_series=True).order_by(Movie.title).all()
    # Lấy danh sách các franchise (series phim)
    all_franchises = Franchise.query.order_by(Franchise.name).all()
    return render_template('admin/add_movie.html', categories=categories, all_series=all_series, all_franchises=all_franchises)

@app.route('/admin/movies/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    if request.method == 'POST':
        old_title = movie.title
        movie.title = request.form.get('title')
        movie.subtitle = request.form.get('subtitle')  # Tiêu đề phụ (tiếng Anh)
        movie.description = request.form.get('description')
        movie.video_url = request.form.get('video_url')
        movie.poster_url = request.form.get('poster_url')
        movie.category_id = request.form.get('category_id') or None
        
        # Franchise (series phim) field
        franchise_id = request.form.get('franchise_id')
        movie.franchise_id = int(franchise_id) if franchise_id else None
        
        # Episodes (phim bộ) fields
        movie.is_series = request.form.get('is_series') == '1'
        series_id = request.form.get('series_id')
        episode_number = request.form.get('episode_number')
        
        if movie.is_series:
            movie.series_id = None
            movie.episode_number = None
        else:
            movie.series_id = int(series_id) if series_id else None
            movie.episode_number = int(episode_number) if episode_number else None
        
        # Handle subtitle URL - only update if a new URL is provided
        new_subtitle_url = request.form.get('subtitle_url', '').strip()
        if new_subtitle_url:
            movie.subtitle_url = new_subtitle_url
        
        # Handle subtitle file upload - this takes priority over URL
        subtitle_file = request.files.get('subtitle')
        if subtitle_file and subtitle_file.filename:
            from werkzeug.utils import secure_filename
            import uuid
            filename = secure_filename(subtitle_file.filename)
            # Add unique prefix to avoid conflicts
            unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
            subtitle_path = os.path.join(app.static_folder, 'uploads', 'subtitles', unique_filename)
            subtitle_file.save(subtitle_path)
            movie.subtitle_url = url_for('static', filename=f'uploads/subtitles/{unique_filename}')
        
        # Tạo lại slug nếu title thay đổi
        if old_title != movie.title or not movie.slug:
            movie.generate_slug()
        
        # Generate url_key nếu chưa có
        if not movie.url_key:
            movie.generate_url_key()
        
        try:
            db.session.commit()
            flash('Cập nhật phim thành công!', 'success')
            return redirect(url_for('admin_movies'))
        except Exception as e:
            db.session.rollback()
            flash('Có lỗi xảy ra.', 'error')
    
    categories = Category.query.all()
    # Lấy danh sách các series (phim bộ), loại trừ phim đang edit
    all_series = Movie.query.filter(Movie.is_series == True, Movie.id != movie_id).order_by(Movie.title).all()
    # Lấy danh sách các franchise (series phim)
    all_franchises = Franchise.query.order_by(Franchise.name).all()
    return render_template('admin/edit_movie.html', movie=movie, categories=categories, all_series=all_series, all_franchises=all_franchises)

@app.route('/admin/movies/delete/<int:movie_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    try:
        db.session.delete(movie)
        db.session.commit()
        flash('Xóa phim thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra.', 'error')
    return redirect(url_for('admin_movies'))

@app.route('/admin/movies/quick-update/<int:movie_id>', methods=['POST'])
@login_required
@admin_required
def admin_quick_update_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    data = request.get_json()
    
    try:
        if 'title' in data:
            movie.title = data['title']
        if 'category_id' in data:
            movie.category_id = data['category_id'] if data['category_id'] else None
        if 'description' in data:
            movie.description = data['description']
        if 'video_url' in data:
            movie.video_url = data['video_url']
        if 'poster_url' in data:
            movie.poster_url = data['poster_url']
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/categories')
@login_required
@admin_required
def admin_categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/add', methods=['POST'])
@login_required
@admin_required
def admin_add_category():
    name = request.form.get('name')
    if not name:
        flash('Vui lòng nhập tên thể loại.', 'error')
        return redirect(url_for('admin_categories'))
    
    # Kiểm tra trùng tên
    existing = Category.query.filter_by(name=name).first()
    if existing:
        flash('Thể loại này đã tồn tại.', 'error')
        return redirect(url_for('admin_categories'))
    
    try:
        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()
        flash('Thêm thể loại thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi thêm thể loại.', 'error')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    try:
        # Set category_id to None for all movies in this category
        for movie in category.movies:
            movie.category_id = None
        db.session.delete(category)
        db.session.commit()
        flash('Xóa thể loại thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi xóa thể loại.', 'error')
    
    return redirect(url_for('admin_categories'))

# Franchise (Series phim) management
@app.route('/admin/franchises')
@login_required
@admin_required
def admin_franchises():
    franchises = Franchise.query.order_by(Franchise.name).all()
    return render_template('admin/franchises.html', franchises=franchises)

@app.route('/admin/franchises/add', methods=['POST'])
@login_required
@admin_required
def admin_add_franchise():
    name = request.form.get('name')
    description = request.form.get('description', '')
    poster_url = request.form.get('poster_url', '')
    
    if not name:
        flash('Vui lòng nhập tên series.', 'error')
        return redirect(url_for('admin_franchises'))
    
    existing = Franchise.query.filter_by(name=name).first()
    if existing:
        flash('Series này đã tồn tại.', 'error')
        return redirect(url_for('admin_franchises'))
    
    try:
        new_franchise = Franchise(name=name, description=description, poster_url=poster_url if poster_url else None)
        db.session.add(new_franchise)
        db.session.commit()
        flash('Thêm series thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi thêm series.', 'error')
    
    return redirect(url_for('admin_franchises'))

@app.route('/admin/franchises/delete/<int:franchise_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_franchise(franchise_id):
    franchise = Franchise.query.get_or_404(franchise_id)
    try:
        for movie in franchise.movies:
            movie.franchise_id = None
        db.session.delete(franchise)
        db.session.commit()
        flash('Xóa series thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi xóa series.', 'error')
    
    return redirect(url_for('admin_franchises'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Bạn không thể thay đổi quyền của chính mình.', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        user.is_admin = not user.is_admin
        db.session.commit()
        status = 'Admin' if user.is_admin else 'User'
        flash(f'Đã cập nhật quyền của {user.username} thành {status}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra.', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Bạn không thể xóa chính mình.', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'Đã xóa người dùng {user.username}!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi xảy ra khi xóa người dùng.', 'error')
    
    return redirect(url_for('admin_users'))

@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

with app.app_context():
    db.create_all()
    
    # Migration: Add columns if not exists
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('movie')]
        
        # Add url_key column
        if 'url_key' not in columns:
            db.session.execute(text('ALTER TABLE movie ADD COLUMN url_key VARCHAR(12)'))
            db.session.commit()
            app.logger.info('Added url_key column to movie table')
            
            try:
                db.session.execute(text('CREATE UNIQUE INDEX ix_movie_url_key ON movie (url_key)'))
                db.session.commit()
            except Exception as idx_err:
                app.logger.warning(f'Index creation note: {idx_err}')
        
        # Add series_id column for episodes
        if 'series_id' not in columns:
            db.session.execute(text('ALTER TABLE movie ADD COLUMN series_id INTEGER REFERENCES movie(id)'))
            db.session.commit()
            app.logger.info('Added series_id column to movie table')
        
        # Add episode_number column
        if 'episode_number' not in columns:
            db.session.execute(text('ALTER TABLE movie ADD COLUMN episode_number INTEGER'))
            db.session.commit()
            app.logger.info('Added episode_number column to movie table')
        
        # Add is_series column
        if 'is_series' not in columns:
            db.session.execute(text('ALTER TABLE movie ADD COLUMN is_series BOOLEAN DEFAULT 0'))
            db.session.commit()
            app.logger.info('Added is_series column to movie table')
        
        # Add franchise_id column
        if 'franchise_id' not in columns:
            db.session.execute(text('ALTER TABLE movie ADD COLUMN franchise_id INTEGER REFERENCES franchise(id)'))
            db.session.commit()
            app.logger.info('Added franchise_id column to movie table')
        
        # Add subtitle column (tiêu đề phụ)
        if 'subtitle' not in columns:
            db.session.execute(text('ALTER TABLE movie ADD COLUMN subtitle VARCHAR(200)'))
            db.session.commit()
            app.logger.info('Added subtitle column to movie table')
        
        # Add display_order column
        if 'display_order' not in columns:
            db.session.execute(text('ALTER TABLE movie ADD COLUMN display_order INTEGER DEFAULT 0'))
            db.session.commit()
            app.logger.info('Added display_order column to movie table')
        
        # Generate url_key for movies that don't have one
        movies_without_key = Movie.query.filter(Movie.url_key == None).all()
        if movies_without_key:
            for movie in movies_without_key:
                movie.generate_url_key()
            db.session.commit()
            app.logger.info(f'Generated url_key for {len(movies_without_key)} movies')
    except Exception as e:
        db.session.rollback()
        app.logger.warning(f'Migration note: {e}')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
