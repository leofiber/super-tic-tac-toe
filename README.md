# 🎯 Super Tic-Tac-Toe Web Application

A sophisticated web-based implementation of Super Tic-Tac-Toe (Ultimate Tic-Tac-Toe) with multiple AI difficulty levels, user authentication, and comprehensive statistics tracking.

## ✨ Features

### 🎮 Game Modes
- **Player vs AI** with three difficulty levels:
  - **Easy**: Random move selection
  - **Medium**: Monte Carlo Tree Search (MCTS) algorithm
  - **Hard**: Advanced AI with deep strategic analysis
- **Local Player vs Player** (coming soon)
- **Online Multiplayer** (planned)

### 👤 User System
- **User Registration & Authentication**
- **Guest Mode** with session-based tracking
- **Persistent Statistics** for registered users
- **Real-time Dashboard** with game stats

### 📊 Analytics & Tracking
- **Comprehensive Statistics**: Win rates, games played, AI difficulty breakdowns
- **Game History**: Track all completed games
- **Performance Metrics**: Detailed analysis per AI difficulty
- **Session Persistence**: Stats survive browser sessions

### 🎨 Modern UI/UX
- **Responsive Design** with Tailwind CSS
- **Interactive Game Board** with visual feedback
- **Real-time Game State Updates**
- **Beautiful Landing Page** and navigation

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/super-tic-tac-toe.git
   cd super-tic-tac-toe
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment** (optional but recommended)
   ```bash
   # Create .env file for secure configuration
   echo "SECRET_KEY=your-unique-secret-key-here" > .env
   echo "FLASK_ENV=development" >> .env
   ```

4. **Initialize the database**
   ```bash
   python tests/init_db.py
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5000`

## 🔒 Security Notes

⚠️ **Important for Production Use:**
- Change the default SECRET_KEY in production
- Test accounts are created with default passwords (`admin/admin123`)
- Database files are excluded from version control
- Environment variables should be used for sensitive configuration

## 📁 Project Structure

```
super-tic-tac-toe/
├── app/                    # Main application package
│   ├── models/            # Database models
│   ├── routes/            # URL routes and views
│   ├── services/          # Business logic layer
│   └── utils/             # Utility functions
├── game/                  # Game engine and AI
│   ├── engine.py         # Core game logic
│   └── advanced_ai.py    # Enhanced AI implementation
├── static/                # Static assets (CSS, JS, images)
├── templates/             # Jinja2 templates
├── tests/                 # Test files and utilities
├── config.py             # Configuration settings
├── run.py               # Application entry point
└── requirements.txt     # Python dependencies
```

## 🎯 Game Rules

Super Tic-Tac-Toe is played on a 3×3 grid of traditional tic-tac-toe boards:

1. **Make your move** on any available cell
2. **Your move determines** which small board your opponent must play on next
3. **Win small boards** by getting three in a row within that board
4. **Win the game** by getting three small boards in a row on the main grid

## 🤖 AI Implementation

### Easy AI
- Random move selection from legal moves
- Perfect for beginners learning the game

### Medium AI  
- Monte Carlo Tree Search (MCTS) algorithm
- Simulates thousands of random games to evaluate moves
- Balanced challenge for intermediate players

### Hard AI
- Advanced strategic analysis with 12+ move lookahead
- Pattern recognition and threat detection
- Enhanced evaluation functions
- Designed to provide expert-level challenge

## 🛠️ Development

### Running Tests
```bash
# Quick system health check
python tests/quick_test.py

# Comprehensive testing
python tests/test_game_system.py
```

### Database Management
```bash
# Reinitialize database (WARNING: destroys all data)
python tests/init_db.py
```

## 🔧 Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Authentication**: Flask-Login with secure password hashing
- **Real-time Features**: Flask-SocketIO (ready for multiplayer)
- **AI Engine**: NumPy-based game logic with advanced algorithms

## 📈 Statistics & Analytics

The application tracks comprehensive statistics:

- **Overall Performance**: Total games, win rate, draws
- **AI Difficulty Breakdown**: Performance against each AI level
- **Game History**: Detailed records of all completed games
- **Time-based Analytics**: Performance trends over time

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Ensure all tests pass**: `python tests/test_game_system.py`
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

## 📄 License

This project is licensed under the MIT License.

---

**Built with ❤️ for strategy game enthusiasts**
