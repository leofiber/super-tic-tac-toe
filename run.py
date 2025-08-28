"""
Main application entry point for Super Tic-Tac-Toe
"""
import os
from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    # Use SocketIO for development server
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
