from flask import Blueprint, render_template, request
from models import Post, Feed, Category
from core.extensions import db
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page showing latest posts from Telegram feeds"""
    page = request.args.get('page', 1, type=int)
    feed_id = request.args.get('feed_id', type=int)
    category_id = request.args.get('category_id', type=int)
    hide_duplicates = request.args.get('hide_duplicates', 'true').lower() == 'true'
    per_page = 10
    
    # Get posts with filters
    query = Post.query
    
    if feed_id:
        query = query.filter_by(feed_id=feed_id)
    elif category_id:
        feed_ids = [f.id for f in Feed.query.filter_by(category_id=category_id).all()]
        if feed_ids:
            query = query.filter(Post.feed_id.in_(feed_ids))
    
    if hide_duplicates:
        query = query.filter(
            (Post.is_primary_duplicate == True) | 
            (Post.duplicate_group_id.is_(None))
        )
    
    posts = query.order_by(Post.telegram_date.desc()).paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Get feeds and categories for sidebar
    feeds = Feed.query.filter_by(is_active=True).order_by(Feed.name).all()
    categories = Category.query.order_by(Category.sort_order, Category.display_name).all()
    
    return render_template('index.html', 
                         posts=posts,
                         feeds=feeds,
                         categories=categories,
                         current_feed_id=feed_id,
                         current_category_id=category_id,
                         hide_duplicates=hide_duplicates)

@main_bp.route('/feed/<int:feed_id>')
def feed_detail(feed_id):
    """Show posts from a specific feed"""
    feed = Feed.query.get_or_404(feed_id)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    posts = Post.query.filter_by(feed_id=feed_id).order_by(
        Post.telegram_date.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('feed_detail.html', feed=feed, posts=posts)

@main_bp.route('/category/<int:category_id>')
def category_detail(category_id):
    """Show posts from feeds in a specific category"""
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    feed_ids = [f.id for f in category.feeds if f.is_active]
    posts = Post.query.filter(Post.feed_id.in_(feed_ids)).order_by(
        Post.telegram_date.desc()
    ).paginate(page=page, per_page=per_page, error_out=False) if feed_ids else None
    
    return render_template('category_detail.html', category=category, posts=posts)

@main_bp.route('/sluzhba')
def sluzhba():
    """Show military service job posts from specific channel"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Target channel URL
    target_channel_url = 'https://t.me/Voyennaya_Rabota_Vakansii'
    
    # Get the specific feed for military jobs
    target_feed = Feed.query.filter_by(url=target_channel_url).first()
    
    if not target_feed:
        # If feed doesn't exist, return empty results
        posts = Post.query.filter(Post.id == -1).paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        # Get posts only from the target channel with duplicate filtering
        posts = Post.query.filter(
            Post.feed_id == target_feed.id
        ).filter(
            (Post.is_primary_duplicate == True) | 
            (Post.duplicate_group_id.is_(None))
        ).order_by(Post.telegram_date.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    return render_template('sluzhba.html', 
                         posts=posts,
                         target_channel=target_channel_url)

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contacts')
def contacts():
    """Contacts page"""
    return render_template('contacts.html')

@main_bp.route('/health')
def health():
    """Health check endpoint for monitoring"""
    from core.extensions import db
    from sqlalchemy import text
    
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500
