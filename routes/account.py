from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import UserPost, UserSubscription, Feed, PostStatistics, PostStatus
from core.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func

account_bp = Blueprint('account', __name__, url_prefix='/account')

@account_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user statistics
    total_posts = UserPost.query.filter_by(user_id=current_user.id).count()
    published_posts = UserPost.query.filter_by(user_id=current_user.id, status=PostStatus.PUBLISHED).count()
    draft_posts = UserPost.query.filter_by(user_id=current_user.id, status=PostStatus.DRAFT).count()
    
    # Get total views for user's posts
    total_views = db.session.query(func.sum(UserPost.views)).filter_by(user_id=current_user.id).scalar() or 0
    
    # Get recent posts
    recent_posts = UserPost.query.filter_by(user_id=current_user.id).order_by(UserPost.created_at.desc()).limit(5).all()
    
    # Get subscriptions count
    subscriptions_count = UserSubscription.query.filter_by(user_id=current_user.id).count()
    
    stats = {
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'total_views': total_views,
        'subscriptions_count': subscriptions_count
    }
    
    return render_template('account/dashboard.html', stats=stats, recent_posts=recent_posts)

@account_bp.route('/posts')
@login_required
def posts():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = UserPost.query.filter_by(user_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=PostStatus(status_filter))
    
    posts = query.order_by(UserPost.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('account/posts.html', posts=posts, status_filter=status_filter)

@account_bp.route('/posts/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', '').strip()
        city = request.form.get('city', '').strip()
        company_name = request.form.get('company_name', '').strip()
        salary_min = request.form.get('salary_min', type=int)
        salary_max = request.form.get('salary_max', type=int)
        contact_phone = request.form.get('contact_phone', '').strip()
        contact_email = request.form.get('contact_email', '').strip()
        contact_telegram = request.form.get('contact_telegram', '').strip()
        action = request.form.get('action', 'draft')
        
        if not title or not content:
            flash('Заголовок и описание обязательны для заполнения', 'error')
            return render_template('account/post_form.html')
        
        post = UserPost(
            user_id=current_user.id,
            title=title,
            content=content,
            category=category if category else None,
            city=city if city else None,
            company_name=company_name if company_name else None,
            salary_min=salary_min,
            salary_max=salary_max,
            contact_phone=contact_phone if contact_phone else None,
            contact_email=contact_email if contact_email else None,
            contact_telegram=contact_telegram if contact_telegram else None,
            status=PostStatus.PUBLISHED if action == 'publish' else PostStatus.DRAFT
        )
        
        if action == 'publish':
            post.published_at = datetime.utcnow()
        
        try:
            db.session.add(post)
            db.session.commit()
            
            if action == 'publish':
                flash('Объявление успешно опубликовано!', 'success')
            else:
                flash('Объявление сохранено как черновик', 'info')
            
            return redirect(url_for('account.posts'))
        
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при сохранении объявления', 'error')
    
    return render_template('account/post_form.html')

@account_bp.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = UserPost.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        post.title = request.form.get('title', '').strip()
        post.content = request.form.get('content', '').strip()
        post.category = request.form.get('category', '').strip() or None
        post.city = request.form.get('city', '').strip() or None
        post.company_name = request.form.get('company_name', '').strip() or None
        post.salary_min = request.form.get('salary_min', type=int)
        post.salary_max = request.form.get('salary_max', type=int)
        post.contact_phone = request.form.get('contact_phone', '').strip() or None
        post.contact_email = request.form.get('contact_email', '').strip() or None
        post.contact_telegram = request.form.get('contact_telegram', '').strip() or None
        post.updated_at = datetime.utcnow()
        
        action = request.form.get('action', 'save')
        
        if action == 'publish' and post.status == PostStatus.DRAFT:
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.utcnow()
        
        if not post.title or not post.content:
            flash('Заголовок и описание обязательны для заполнения', 'error')
            return render_template('account/post_form.html', post=post)
        
        try:
            db.session.commit()
            flash('Объявление успешно обновлено!', 'success')
            return redirect(url_for('account.posts'))
        
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при обновлении объявления', 'error')
    
    return render_template('account/post_form.html', post=post)

@account_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = UserPost.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(post)
        db.session.commit()
        flash('Объявление успешно удалено', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Произошла ошибка при удалении объявления', 'error')
    
    return redirect(url_for('account.posts'))

@account_bp.route('/subscriptions')
@login_required
def subscriptions():
    user_subscriptions = UserSubscription.query.filter_by(user_id=current_user.id).all()
    available_feeds = Feed.query.filter(~Feed.id.in_([s.feed_id for s in user_subscriptions])).all()
    
    return render_template('account/subscriptions.html', 
                         subscriptions=user_subscriptions, 
                         available_feeds=available_feeds)

@account_bp.route('/subscriptions/add', methods=['POST'])
@login_required
def add_subscription():
    feed_id = request.form.get('feed_id', type=int)
    
    if not feed_id:
        flash('Выберите канал для подписки', 'error')
        return redirect(url_for('account.subscriptions'))
    
    # Check if subscription already exists
    existing = UserSubscription.query.filter_by(user_id=current_user.id, feed_id=feed_id).first()
    if existing:
        flash('Вы уже подписаны на этот канал', 'warning')
        return redirect(url_for('account.subscriptions'))
    
    subscription = UserSubscription(user_id=current_user.id, feed_id=feed_id)
    
    try:
        db.session.add(subscription)
        db.session.commit()
        flash('Подписка успешно добавлена!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Произошла ошибка при добавлении подписки', 'error')
    
    return redirect(url_for('account.subscriptions'))

@account_bp.route('/subscriptions/<int:subscription_id>/delete', methods=['POST'])
@login_required
def delete_subscription(subscription_id):
    subscription = UserSubscription.query.filter_by(
        id=subscription_id, 
        user_id=current_user.id
    ).first_or_404()
    
    try:
        db.session.delete(subscription)
        db.session.commit()
        flash('Подписка отменена', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Произошла ошибка при отмене подписки', 'error')
    
    return redirect(url_for('account.subscriptions'))

@account_bp.route('/statistics')
@login_required
def statistics():
    # Get post statistics for the last 30 days
    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
    
    # Get daily statistics
    daily_stats = db.session.query(
        PostStatistics.date,
        func.sum(PostStatistics.views).label('total_views'),
        func.sum(PostStatistics.clicks).label('total_clicks'),
        func.sum(PostStatistics.contact_views).label('total_contact_views')
    ).join(UserPost).filter(
        UserPost.user_id == current_user.id,
        PostStatistics.date >= thirty_days_ago
    ).group_by(PostStatistics.date).order_by(PostStatistics.date).all()
    
    # Get top performing posts
    top_posts = db.session.query(
        UserPost.title,
        UserPost.views,
        func.sum(PostStatistics.clicks).label('total_clicks')
    ).outerjoin(PostStatistics).filter(
        UserPost.user_id == current_user.id
    ).group_by(UserPost.id).order_by(UserPost.views.desc()).limit(10).all()
    
    return render_template('account/statistics.html', 
                         daily_stats=daily_stats, 
                         top_posts=top_posts)

@account_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', '').strip() or None
        current_user.last_name = request.form.get('last_name', '').strip() or None
        current_user.phone = request.form.get('phone', '').strip() or None
        current_user.telegram_username = request.form.get('telegram_username', '').strip() or None
        current_user.updated_at = datetime.utcnow()
        
        # Handle password change
        new_password = request.form.get('new_password', '')
        if new_password:
            current_password = request.form.get('current_password', '')
            if not current_user.check_password(current_password):
                flash('Неверный текущий пароль', 'error')
                return render_template('account/profile.html')
            
            if len(new_password) < 6:
                flash('Новый пароль должен содержать минимум 6 символов', 'error')
                return render_template('account/profile.html')
            
            current_user.set_password(new_password)
        
        try:
            db.session.commit()
            flash('Профиль успешно обновлен!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при обновлении профиля', 'error')
    
    return render_template('account/profile.html')
