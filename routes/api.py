from flask import Blueprint, jsonify, request
from models.post import Post
from models.feed import Feed
from models.category import Category

api_bp = Blueprint('api', __name__)

@api_bp.route('/posts')
def get_posts():
    """API endpoint to get posts with filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    feed_id = request.args.get('feed_id', type=int)
    category_id = request.args.get('category_id', type=int)
    hide_duplicates = request.args.get('hide_duplicates', 'false').lower() == 'true'
    search = request.args.get('search', '')
    
    # Limit per_page to reasonable values
    per_page = min(per_page, 100)
    offset = (page - 1) * per_page
    
    # Build query
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
    
    if search:
        query = query.filter(Post.content.contains(search))
    
    # Get results
    posts = query.order_by(Post.telegram_date.desc()).offset(offset).limit(per_page).all()
    total = query.count()
    
    return jsonify({
        'posts': [post.to_dict() for post in posts],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })

@api_bp.route('/feeds')
def get_feeds():
    """API endpoint to get all feeds"""
    feeds = Feed.query.filter_by(is_active=True).order_by(Feed.name).all()
    return jsonify([feed.to_dict() for feed in feeds])

@api_bp.route('/categories')
def get_categories():
    """API endpoint to get all categories"""
    categories = Category.query.order_by(Category.sort_order, Category.display_name).all()
    return jsonify([category.to_dict() for category in categories])

@api_bp.route('/feeds/<int:feed_id>')
def get_feed(feed_id):
    """API endpoint to get a specific feed"""
    feed = Feed.query.get_or_404(feed_id)
    return jsonify(feed.to_dict())

@api_bp.route('/stats')
def get_stats():
    """API endpoint to get basic statistics"""
    return jsonify({
        'total_posts': Post.query.count(),
        'total_feeds': Feed.query.filter_by(is_active=True).count(),
        'total_categories': Category.query.count(),
        'recent_posts': Post.query.order_by(Post.created_at.desc()).limit(5).count()
    })
