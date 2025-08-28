"""
API routes for AJAX requests
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import User, Game, Room
from app.services import GameService

api_bp = Blueprint('api', __name__)
game_service = GameService()

@api_bp.route('/user/stats')
@login_required
def user_stats():
    """Get current user statistics."""
    return jsonify(current_user.to_dict())

@api_bp.route('/leaderboard')
def leaderboard():
    """Get top players leaderboard."""
    top_players = User.query.filter(User.games_played > 0).order_by(
        User.win_rate.desc(), User.games_won.desc()
    ).limit(10).all()
    
    return jsonify([{
        'username': user.username,
        'games_played': user.games_played,
        'games_won': user.games_won,
        'win_rate': user.win_rate
    } for user in top_players])

@api_bp.route('/rooms/available')
def available_rooms():
    """Get list of available public rooms."""
    rooms = Room.query.filter_by(
        is_private=False,
        status='waiting'
    ).filter(Room.guest_id.is_(None)).all()
    
    return jsonify([room.to_dict() for room in rooms])

@api_bp.route('/user/settings', methods=['POST'])
@login_required
def update_settings():
    """Update user settings."""
    data = request.get_json()
    
    if 'theme' in data:
        current_user.preferred_theme = data['theme']
    
    if 'sound_enabled' in data:
        current_user.sound_enabled = bool(data['sound_enabled'])
    
    from app import db
    db.session.commit()
    
    return jsonify({'success': True})
