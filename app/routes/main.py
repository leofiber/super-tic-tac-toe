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
    # Get comprehensive statistics for the landing page (with error handling)
    try:
        # Basic counts from database
        total_users = User.query.count()
        total_db_games = Game.query.count()
        
        # Game type breakdown (real database values only)
        pvai_games = Game.query.filter_by(game_type='pvai').count()
        pvp_local_games = Game.query.filter_by(game_type='pvp_local').count()
        pvp_online_games = Game.query.filter_by(game_type='pvp_online').count()
        
        # AI difficulty breakdown (real database values only)
        easy_ai_games = Game.query.filter_by(game_type='pvai', ai_difficulty='easy').count()
        medium_ai_games = Game.query.filter_by(game_type='pvai', ai_difficulty='medium').count()
        hard_ai_games = Game.query.filter_by(game_type='pvai', ai_difficulty='hard').count()
        
        # Guest games: For now, we'll track this via session data or analytics
        # This is a placeholder - in production you'd implement proper guest game tracking
        from flask import session
        guest_games_count = session.get('guest_games_played', 0)
        
        # Total games = database games + session-tracked guest games
        total_games = total_db_games + guest_games_count
        
        # Active players (users who logged in recently)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_players = User.query.filter(User.last_seen >= thirty_days_ago).count()
        
        # If no users are active, at least show current user if logged in
        if active_players == 0 and total_users > 0:
            active_players = min(total_users, 1)
        
        # Total AI games (sum of all difficulties)
        total_ai_games = easy_ai_games + medium_ai_games + hard_ai_games
        
        stats = {
            'total_games': total_games,
            'total_users': total_users,
            'active_players': active_players,
            'total_ai_games': total_ai_games,
            'pvai_games': pvai_games,
            'pvp_local_games': pvp_local_games,
            'pvp_online_games': pvp_online_games,
            'easy_ai_games': easy_ai_games,
            'medium_ai_games': medium_ai_games,
            'hard_ai_games': hard_ai_games
        }
        
    except Exception as e:
        # Database might not be initialized yet
        print(f"Error getting landing page stats: {e}")
        stats = {
            'total_games': 0,
            'total_users': 0,
            'active_players': 0,
            'total_ai_games': 0,
            'pvai_games': 0,
            'pvp_local_games': 0,
            'pvp_online_games': 0,
            'easy_ai_games': 0,
            'medium_ai_games': 0,
            'hard_ai_games': 0
        }
    
    return render_template('landing.html', **stats)

@main_bp.route('/dashboard')
def dashboard():
    """User dashboard with game options."""
    # Import here to avoid circular imports
    from app.routes.game import get_user_stats
    from flask import session
    
    if current_user and current_user.is_authenticated:
        # Registered user: get recent games from database with proper joins
        recent_games = Game.query.filter(
            (Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)
        ).filter(Game.winner.isnot(None)).order_by(Game.finished_at.desc().nullslast(), Game.created_at.desc()).limit(5).all()
        
        guest_stats = None
    else:
        # Guest user: get recent games from session
        try:
            stats = get_user_stats()
            recent_games = stats.get('recent_games', [])
            guest_stats = {
                'games_played': stats.get('total_games', 0),
                'games_won': stats.get('victories', 0),
                'games_drawn': stats.get('draws', 0),
                'win_rate': stats.get('win_rate', 0),
                'recent_games': recent_games
            }
        except Exception as e:
            # Fallback for edge cases
            print(f"Error getting guest stats: {e}")
            recent_games = []
            guest_stats = {
                'games_played': 0,
                'games_won': 0,
                'games_drawn': 0,
                'win_rate': 0,
                'recent_games': []
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
