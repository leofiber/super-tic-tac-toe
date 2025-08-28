"""
Room service for managing multiplayer rooms
"""
from app import db
from app.models import Room, User

class RoomService:
    """Service for managing game rooms."""
    
    @staticmethod
    def create_room(host_id, is_private=False, allow_spectators=True):
        """Create a new game room."""
        room = Room(
            code=Room.generate_code(),
            host_id=host_id,
            is_private=is_private,
            allow_spectators=allow_spectators
        )
        
        db.session.add(room)
        db.session.commit()
        return room
    
    @staticmethod
    def join_room(room_code, user_id):
        """Join an existing room."""
        room = Room.query.filter_by(code=room_code.upper()).first()
        
        if not room:
            return None, "Room not found"
        
        if room.is_full:
            return None, "Room is full"
        
        if room.add_player(User.query.get(user_id)):
            return room, "Successfully joined room"
        else:
            return None, "Could not join room"
    
    @staticmethod
    def get_available_rooms():
        """Get list of available public rooms."""
        return Room.query.filter_by(
            is_private=False,
            status='waiting'
        ).filter(Room.guest_id.is_(None)).all()
    
    @staticmethod
    def cleanup_expired_rooms():
        """Remove expired rooms."""
        expired_rooms = Room.query.filter(Room.is_expired == True).all()
        for room in expired_rooms:
            db.session.delete(room)
        db.session.commit()
        return len(expired_rooms)
