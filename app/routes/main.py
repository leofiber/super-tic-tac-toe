"""
Main routes for landing page and general pages
"""
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user
from app.models import User, Game
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing():
    """Landing page with game overview."""
    # Get some statistics for the landing page (with error handling)
    try:
        total_games = Game.query.count()
        total_users = User.query.count()
    except:
        # Database might not be initialized yet
        total_games = 0
        total_users = 0
    
    return render_template('landing.html', 
                         total_games=total_games, 
                         total_users=total_users)

@main_bp.route('/dashboard')
def dashboard():
    """User dashboard with game options."""
    # Import here to avoid circular imports
    from app.routes.game import get_user_stats
    from flask import session
    
    if current_user and current_user.is_authenticated:
        # Registered user: get recent games from database
        recent_games = Game.query.filter(
            (Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)
        ).filter(Game.winner.isnot(None)).order_by(Game.created_at.desc()).limit(5).all()
        guest_stats = None
    else:
        # Guest user: get recent games from session
        try:
            stats = get_user_stats()
            recent_games = stats.get('recent_games', [])
            guest_stats = {
                'games_played': session.get('games_played', 0),
                'games_won': session.get('games_won', 0),
                'games_drawn': session.get('games_drawn', 0),
                'win_rate': (session.get('games_won', 0) * 100 / session.get('games_played', 1)) if session.get('games_played', 0) > 0 else 0
            }
        except:
            # Fallback for edge cases (like testing without proper session)
            recent_games = []
            guest_stats = {
                'games_played': 0,
                'games_won': 0,
                'games_drawn': 0,
                'win_rate': 0
            }
    
    return render_template('dashboard.html', recent_games=recent_games, guest_stats=guest_stats)

@main_bp.route('/play')
def play_options():
    """Game mode selection page."""
    return render_template('play_options.html')

@main_bp.route('/statistics')
def statistics():
    """Statistics page."""
    # Import here to avoid circular imports
    from app.routes.game import get_user_stats
    
    stats = get_user_stats()
    return render_template('statistics.html', user=current_user, stats=stats)

@main_bp.route('/about')
def about():
    """About page with game rules."""
    return render_template('about.html')

@main_bp.route('/settings')
def settings():
    """User settings page."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    return render_template('settings.html', user=current_user)
