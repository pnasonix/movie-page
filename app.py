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

app = Flask(__name__)
# Sử dụng environment variable cho SECRET_KEY, fallback về giá trị mặc định
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///movies.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable cache for static files in development
app.config['CSS_VERSION'] = os.environ.get('CSS_VERSION', '7.0')  # CSS version for cache busting
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto-reload templates in development
app.jinja_env.auto_reload = True  # Enable Jinja2 auto-reload

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'

# Đảm bảo thư mục upload tồn tại
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'movies'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'posters'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)

# Logging cấu hình: ghi log ứng dụng vào instance/app.log
try:
    os.makedirs(app.instance_path, exist_ok=True)
    log_file = os.path.join(app.instance_path, 'app.log')
    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    if not app.logger.handlers:
        app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application logging initialized')
except Exception:
    # Không để logging lỗi làm hỏng app
    pass

# Models
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

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    video_url = db.Column(db.String(500))
    poster_url = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    watch_history = db.relationship('WatchHistory', backref='movie', lazy=True)

class WatchHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    watched_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_position = db.Column(db.Integer, default=0)  # Thời gian xem cuối cùng (giây)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_favorite'),)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Ensure tables exist when running under gunicorn
try:
    with app.app_context():
        db.create_all()
except Exception:
    pass

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context processor để categories có sẵn trong tất cả templates
@app.context_processor
def inject_categories():
    try:
    categories = Category.query.order_by(Category.name.asc()).all()
    except Exception:
        # Nếu DB gặp lỗi (vd: SQLite locked), không để 500
        db.session.rollback()
        categories = []
    return dict(categories=categories)

# Context processor để tự động cập nhật CSS và JS version dựa trên file modification time
@app.context_processor
def inject_static_versions():
    def get_file_version(filename):
        file_path = os.path.join(app.static_folder, filename)
        try:
            # Lấy timestamp của file (modification time)
            file_mtime = os.path.getmtime(file_path)
            # Chuyển thành version number (timestamp)
            return str(int(file_mtime))
        except (OSError, ValueError):
            # Fallback nếu không tìm thấy file
            return str(int(datetime.now().timestamp()))
    
    return dict(
        css_version=get_file_version('css/style.css'),
        js_version=get_file_version('js/main.js')
    )

# Routes
@app.route('/')
def index():
    try:
    categories = Category.query.all()
    except Exception:
        db.session.rollback()
        categories = []
    filter_type = request.args.get('filter', 'all')  # all, popular, newest
    try:
    if filter_type == 'popular':
        movies = Movie.query.order_by(Movie.views.desc()).all()
    elif filter_type == 'newest':
        movies = Movie.query.order_by(Movie.created_at.desc()).all()
        elif filter_type == 'watched' and current_user.is_authenticated:
            # Lấy danh sách phim đã xem theo thứ tự thời gian xem gần nhất, không trùng lặp
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
            # Lấy danh sách phim đã thích theo thời gian thích gần nhất
            fav_rows = db.session.query(Favorite, Movie).join(
                Movie, Favorite.movie_id == Movie.id
            ).filter(
                Favorite.user_id == current_user.id
            ).order_by(Favorite.created_at.desc()).limit(100).all()
            movies = [movie for _, movie in fav_rows]
    else:  # all
        movies = Movie.query.order_by(Movie.created_at.desc()).all()
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
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('login'))
    
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
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công.', 'success')
    return redirect(url_for('index'))

@app.route('/movie/<int:movie_id>')
def movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    # Tăng lượt xem nhưng không để lỗi DB làm hỏng trang xem
    try:
    movie.views += 1
    db.session.commit()
    except Exception:
        db.session.rollback()
    
    # Lấy lịch sử xem nếu user đã đăng nhập
    last_position = 0
    is_favorite = False
    if current_user.is_authenticated:
        try:
        history = WatchHistory.query.filter_by(
            user_id=current_user.id,
            movie_id=movie_id
        ).first()
        if history:
            last_position = history.last_position
        except Exception:
            db.session.rollback()
            last_position = 0
        try:
        # Kiểm tra xem user đã thích phim này chưa
        favorite = Favorite.query.filter_by(
            user_id=current_user.id,
            movie_id=movie_id
        ).first()
        is_favorite = favorite is not None
        except Exception:
            db.session.rollback()
            is_favorite = False
    
    # Lấy phim liên quan (cùng thể loại)
    try:
    related_movies = Movie.query.filter(
        Movie.category_id == movie.category_id,
        Movie.id != movie_id
    ).limit(6).all()
    except Exception:
        db.session.rollback()
        related_movies = []
    
    return render_template('movie.html', movie=movie, last_position=last_position, related_movies=related_movies, is_favorite=is_favorite)

# Route /watch đã được xóa - sử dụng /movie/<id> làm trang xem phim chính
@app.route('/watch/<int:movie_id>')
def watch_legacy_path(movie_id):
    # Redirect vĩnh viễn các đường dẫn cũ sang route mới
    return redirect(url_for('movie', movie_id=movie_id), code=301)

@app.route('/watch')
def watch_legacy_query():
    # Hỗ trợ dạng /watch?id=123 hoặc /watch?movie_id=123
    movie_id = request.args.get('id') or request.args.get('movie_id')
    if movie_id and str(movie_id).isdigit():
        return redirect(url_for('movie', movie_id=int(movie_id)), code=301)
    flash('Đường dẫn xem phim không hợp lệ.', 'error')
    return redirect(url_for('index'))

@app.route('/xem-phim/<int:movie_id>')
def xem_phim_legacy(movie_id):
    # Hỗ trợ đường dẫn tiếng Việt cũ
    return redirect(url_for('movie', movie_id=movie_id), code=301)

@app.route('/save_watch_position', methods=['POST'])
@login_required
def save_watch_position():
    data = request.get_json()
    movie_id = data.get('movie_id')
    position = data.get('position', 0)
    
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
    return jsonify({'success': True})

@app.route('/profile')
@login_required
def profile():
    # Lấy watch history với join để đảm bảo movie còn tồn tại
    try:
    watch_history = db.session.query(WatchHistory).join(
        Movie, WatchHistory.movie_id == Movie.id
    ).filter(
        WatchHistory.user_id == current_user.id
    ).order_by(WatchHistory.watched_at.desc()).limit(20).all()
    except Exception:
        db.session.rollback()
        watch_history = []
    
    # Lấy danh sách phim đã thích
    try:
        liked_movies = db.session.query(Movie).join(
            Favorite, Favorite.movie_id == Movie.id
        ).filter(
            Favorite.user_id == current_user.id
        ).order_by(Favorite.created_at.desc()).all()
    except Exception:
        db.session.rollback()
        liked_movies = []
    
    return render_template('profile.html', watch_history=watch_history, liked_movies=liked_movies)

@app.route('/toggle_like', methods=['POST'])
@login_required
def toggle_like():
    data = request.get_json()
    movie_id = data.get('movie_id')
    
    if not movie_id:
        return jsonify({'success': False, 'error': 'Movie ID is required'}), 400
    
    movie = Movie.query.get_or_404(movie_id)
    
    # Kiểm tra xem đã thích chưa
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()
    
    if favorite:
        # Bỏ thích
        db.session.delete(favorite)
        is_favorite = False
    else:
        # Thêm vào danh sách yêu thích
        favorite = Favorite(
            user_id=current_user.id,
            movie_id=movie_id
        )
        db.session.add(favorite)
        is_favorite = True
    
    db.session.commit()
    return jsonify({'success': True, 'is_favorite': is_favorite})

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    avatar_url = request.form.get('avatar_url')
    
    # Validate
    if not username or not email:
        flash('Vui lòng điền đầy đủ thông tin.', 'error')
        return redirect(url_for('profile'))
    
    # Kiểm tra username đã tồn tại chưa (trừ user hiện tại)
    existing_user = User.query.filter(
        User.username == username,
        User.id != current_user.id
    ).first()
    if existing_user:
        flash('Tên người dùng đã được sử dụng.', 'error')
        return redirect(url_for('profile'))
    
    # Kiểm tra email đã tồn tại chưa (trừ user hiện tại)
    existing_email = User.query.filter(
        User.email == email,
        User.id != current_user.id
    ).first()
    if existing_email:
        flash('Email đã được sử dụng.', 'error')
        return redirect(url_for('profile'))
    
    # Cập nhật thông tin
    current_user.username = username
    current_user.email = email
    if avatar_url:
        current_user.avatar_url = avatar_url
    
    db.session.commit()
    flash('Đã cập nhật thông tin thành công!', 'success')
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate inputs
    if not current_password or not new_password or not confirm_password:
        flash('Vui lòng điền đầy đủ thông tin.', 'error')
        return redirect(url_for('profile'))
    
    # Check if new password matches confirmation
    if new_password != confirm_password:
        flash('Mật khẩu mới và xác nhận mật khẩu không khớp.', 'error')
        return redirect(url_for('profile'))
    
    # Check password length
    if len(new_password) < 6:
        flash('Mật khẩu phải có ít nhất 6 ký tự.', 'error')
        return redirect(url_for('profile'))
    
    # Verify current password
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Mật khẩu hiện tại không đúng.', 'error')
        return redirect(url_for('profile'))
    
    # Update password
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    flash('Đã đổi mật khẩu thành công!', 'success')
    return redirect(url_for('profile'))

@app.route('/category/<int:category_id>')
def category_movies(category_id):
    category = Category.query.get_or_404(category_id)
    movies = Movie.query.filter_by(category_id=category_id).all()
    return render_template('category.html', category=category, movies=movies)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        movies = Movie.query.filter(
            Movie.title.contains(query) | Movie.description.contains(query)
        ).all()
    else:
        movies = []
    return render_template('search.html', movies=movies, query=query)

# Favorites
@app.route('/favorites')
@login_required
def favorites():
    try:
        movies = db.session.query(Movie).join(
            Favorite, Favorite.movie_id == Movie.id
        ).filter(
            Favorite.user_id == current_user.id
        ).order_by(Favorite.created_at.desc()).all()
    except Exception:
        db.session.rollback()
        movies = []
    return render_template('favorites.html', movies=movies)

# Comments API
@app.route('/comments', methods=['GET'])
def get_comments():
    try:
        movie_id = request.args.get('movie_id', type=int)
        if not movie_id:
            return jsonify({'success': False, 'error': 'movie_id is required'}), 400
        # Ensure movie exists
        movie = Movie.query.get(movie_id)
        if not movie:
            return jsonify({'success': False, 'error': 'Movie not found'}), 404
        comments = db.session.query(Comment, User).join(User, Comment.user_id == User.id).filter(
            Comment.movie_id == movie_id
        ).order_by(Comment.created_at.desc()).limit(100).all()
        items = []
        for c, u in comments:
            items.append({
                'id': c.id,
                'user': {'id': u.id, 'username': u.username, 'avatar_url': u.avatar_url},
                'content': c.content,
                'created_at': c.created_at.isoformat() + 'Z'
            })
        return jsonify({'success': True, 'comments': items})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Server error'}), 500

@app.route('/comments', methods=['POST'])
@login_required
def post_comment():
    try:
        data = request.get_json() or {}
        movie_id = data.get('movie_id')
        content = (data.get('content') or '').strip()
        if not movie_id:
            return jsonify({'success': False, 'error': 'movie_id is required'}), 400
        if not content:
            return jsonify({'success': False, 'error': 'Nội dung không được để trống'}), 400
        if len(content) > 1000:
            return jsonify({'success': False, 'error': 'Nội dung quá dài (tối đa 1000 ký tự)'}), 400
        movie = Movie.query.get(movie_id)
        if not movie:
            return jsonify({'success': False, 'error': 'Movie not found'}), 404
        comment = Comment(user_id=current_user.id, movie_id=movie_id, content=content)
        db.session.add(comment)
        db.session.commit()
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'avatar_url': current_user.avatar_url
                },
                'content': comment.content,
                'created_at': comment.created_at.isoformat() + 'Z'
            }
        })
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Server error'}), 500

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    try:
        if not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        comment = Comment.query.get_or_404(comment_id)
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'success': True})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Server error'}), 500

# Upload avatar
@app.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    try:
        if 'avatar_file' not in request.files:
            flash('Không tìm thấy file tải lên.', 'error')
            return redirect(url_for('profile'))
        file = request.files['avatar_file']
        if not file or not file.filename:
            flash('Vui lòng chọn một ảnh để tải lên.', 'error')
            return redirect(url_for('profile'))
        # Validate extension
        allowed_ext = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in allowed_ext:
            flash('Định dạng ảnh không hợp lệ. Chỉ hỗ trợ JPG, PNG, GIF, WEBP.', 'error')
            return redirect(url_for('profile'))
        # Save with timestamp prefix
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stored_name = f"{timestamp}_{filename}"
        save_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars')
        save_path = os.path.join(save_dir, stored_name)
        file.save(save_path)
        # Build public URL
        avatar_url = url_for('static', filename=f'uploads/avatars/{stored_name}')
        # Update user
        current_user.avatar_url = avatar_url
        db.session.commit()
        flash('Tải lên avatar thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Có lỗi khi tải lên avatar.', 'error')
    return redirect(url_for('profile'))
# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    try:
        app.logger.warning(f'404 Not Found: {request.path}')
    except Exception:
        pass
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    try:
        app.logger.exception('500 Internal Server Error')
    except Exception:
        pass
    return render_template('errors/500.html'), 500

# Admin routes
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bạn cần quyền admin để truy cập trang này.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_movies = Movie.query.count()
    total_users = User.query.count()
    total_views = db.session.query(db.func.sum(Movie.views)).scalar() or 0
    recent_movies = Movie.query.order_by(Movie.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', 
                         total_movies=total_movies,
                         total_users=total_users,
                         total_views=total_views,
                         recent_movies=recent_movies)

@app.route('/admin/movies')
@login_required
@admin_required
def admin_movies():
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    categories = Category.query.all()
    return render_template('admin/movies.html', movies=movies, categories=categories)

@app.route('/admin/movies/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_movie():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        video_url = request.form.get('video_url')
        category_id = request.form.get('category_id')
        poster_url = request.form.get('poster_url')
        
        # Handle poster upload
        if 'poster' in request.files:
            file = request.files['poster']
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posters', filename)
                file.save(filepath)
                poster_url = url_for('static', filename=f'uploads/posters/{filename}')
        
        # Handle video upload
        if 'video' in request.files:
            file = request.files['video']
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'movies', filename)
                file.save(filepath)
                video_url = url_for('static', filename=f'uploads/movies/{filename}')
        
        if not title or not video_url:
            flash('Vui lòng điền đầy đủ thông tin bắt buộc.', 'error')
            return redirect(url_for('admin_add_movie'))
        
        movie = Movie(
            title=title,
            description=description,
            video_url=video_url,
            poster_url=poster_url or 'https://via.placeholder.com/300x450?text=No+Image',
            category_id=int(category_id) if category_id else None
        )
        
        db.session.add(movie)
        db.session.commit()
        flash('Đã thêm phim thành công!', 'success')
        return redirect(url_for('admin_movies'))
    
    categories = Category.query.all()
    return render_template('admin/add_movie.html', categories=categories)

@app.route('/admin/movies/<int:movie_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    if request.method == 'POST':
        movie.title = request.form.get('title')
        movie.description = request.form.get('description')
        movie.video_url = request.form.get('video_url')
        movie.category_id = int(request.form.get('category_id')) if request.form.get('category_id') else None
        movie.poster_url = request.form.get('poster_url')
        
        # Handle poster upload
        if 'poster' in request.files:
            file = request.files['poster']
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'posters', filename)
                file.save(filepath)
                movie.poster_url = url_for('static', filename=f'uploads/posters/{filename}')
        
        # Handle video upload
        if 'video' in request.files:
            file = request.files['video']
            if file and file.filename:
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'movies', filename)
                file.save(filepath)
                movie.video_url = url_for('static', filename=f'uploads/movies/{filename}')
        
        db.session.commit()
        flash('Đã cập nhật phim thành công!', 'success')
        return redirect(url_for('admin_movies'))
    
    categories = Category.query.all()
    return render_template('admin/edit_movie.html', movie=movie, categories=categories)

@app.route('/admin/movies/<int:movie_id>/quick_update', methods=['POST'])
@login_required
@admin_required
def admin_quick_update_movie(movie_id):
    try:
        movie = Movie.query.get_or_404(movie_id)
        data = request.get_json() or {}
        title = data.get('title')
        category_id = data.get('category_id')
        updated = {}
        if title is not None:
            movie.title = title.strip()
            updated['title'] = movie.title
        if category_id is not None:
            movie.category_id = int(category_id) if str(category_id).isdigit() else None
            updated['category_id'] = movie.category_id
        db.session.commit()
        return jsonify({'success': True, 'movie': {'id': movie.id, **updated}})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Không thể cập nhật nhanh'}), 500

@app.route('/admin/movies/<int:movie_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_movie(movie_id):
    try:
        # Hoàn toàn tách khỏi ORM để tránh flush cập nhật NULL vào FK
        db.session.remove()
        with db.engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys = OFF"))
            conn.execute(text("DELETE FROM watch_history WHERE movie_id = :mid"), {'mid': movie_id})
            conn.execute(text("DELETE FROM favorite WHERE movie_id = :mid"), {'mid': movie_id})
            conn.execute(text("DELETE FROM comment WHERE movie_id = :mid"), {'mid': movie_id})
            conn.execute(text("DELETE FROM movie WHERE id = :mid"), {'mid': movie_id})
            conn.execute(text("PRAGMA foreign_keys = ON"))
    flash('Đã xóa phim thành công!', 'success')
    except Exception:
        db.session.rollback()
        flash('Không thể xóa phim do lỗi hệ thống hoặc ràng buộc dữ liệu.', 'error')
    return redirect(url_for('admin_movies'))

@app.route('/admin/movies/bulk_delete', methods=['POST'])
@login_required
@admin_required
def admin_bulk_delete_movies():
    try:
        db.session.remove()
        with db.engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys = OFF"))
            conn.execute(text("DELETE FROM watch_history"))
            conn.execute(text("DELETE FROM favorite"))
            conn.execute(text("DELETE FROM comment"))
            conn.execute(text("DELETE FROM movie"))
            conn.execute(text("PRAGMA foreign_keys = ON"))
        flash('Đã xóa TẤT CẢ phim và dữ liệu liên quan.', 'success')
    except Exception:
        db.session.rollback()
        flash('Không thể xóa tất cả phim do lỗi hệ thống.', 'error')
    return redirect(url_for('admin_movies'))
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
    if name:
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        flash('Đã thêm thể loại thành công!', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Đã xóa thể loại thành công!', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/toggle_admin', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Bạn không thể thay đổi quyền admin của chính mình.', 'error')
        return redirect(url_for('admin_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    status = 'admin' if user.is_admin else 'người dùng thường'
    flash(f'Đã cập nhật {user.username} thành {status}!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Bạn không thể xóa chính mình.', 'error')
        return redirect(url_for('admin_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'Đã xóa người dùng {username} thành công!', 'success')
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Tạo dữ liệu mẫu nếu chưa có
        if Category.query.count() == 0:
            categories = [
                Category(name='Hành động'),
                Category(name='Tình cảm'),
                Category(name='Hài hước'),
                Category(name='Kinh dị'),
                Category(name='Khoa học viễn tưởng'),
                Category(name='Phiêu lưu')
            ]
            for cat in categories:
                db.session.add(cat)
            db.session.commit()
        
        if Movie.query.count() == 0:
            action_cat = Category.query.filter_by(name='Hành động').first()
            if action_cat:
                sample_movies = [
                    Movie(
                        title='Phim Hành Động 1',
                        description='Một bộ phim hành động đầy kịch tính với những pha võ thuật ngoạn mục.',
                        video_url='https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
                        poster_url='https://via.placeholder.com/300x450?text=Movie+1',
                        category_id=action_cat.id
                    ),
                    Movie(
                        title='Phim Tình Cảm 1',
                        description='Câu chuyện tình yêu cảm động về hai người yêu nhau.',
                        video_url='https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4',
                        poster_url='https://via.placeholder.com/300x450?text=Movie+2',
                        category_id=Category.query.filter_by(name='Tình cảm').first().id if Category.query.filter_by(name='Tình cảm').first() else action_cat.id
                    )
                ]
                for movie in sample_movies:
                    db.session.add(movie)
                db.session.commit()
    
    # Development mode: auto-reload on file changes
    # Port 5001 để match với nginx proxy
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=True, use_debugger=True)

