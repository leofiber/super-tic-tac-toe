#!/usr/bin/env python3
"""
Comprehensive automated testing for the Super Tic-Tac-Toe game system
Tests all the functionality without requiring manual gameplay
"""

import requests
import json
import time
import random
from datetime import datetime

class GameSystemTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_all(self):
        """Run all tests and report results."""
        print("🧪 Starting Comprehensive Game System Tests")
        print("=" * 50)
        
        results = {}
        
        # Test 1: Guest game logging
        print("\n1️⃣ Testing Guest Game Logging...")
        results['guest_logging'] = self.test_guest_game_logging()
        
        # Test 2: User registration and account creation
        print("\n2️⃣ Testing New User Registration...")
        results['user_registration'] = self.test_user_registration()
        
        # Test 3: Logged-in user game logging
        print("\n3️⃣ Testing Logged-in User Game Logging...")
        results['logged_user_logging'] = self.test_logged_user_game_logging()
        
        # Test 4: Database table creation for new users
        print("\n4️⃣ Testing Database Tables for New Users...")
        results['db_tables'] = self.test_database_tables()
        
        # Test 5: Stats accuracy on dashboard
        print("\n5️⃣ Testing Stats Dashboard Accuracy...")
        results['stats_accuracy'] = self.test_stats_accuracy()
        
        # Test 6: Game completion (no hanging)
        print("\n6️⃣ Testing Game Completion...")
        results['game_completion'] = self.test_game_completion()
        
        # Test 7: AI difficulty comparison
        print("\n7️⃣ Testing AI Difficulty Levels...")
        results['ai_difficulty'] = self.test_ai_difficulty()
        
        # Print summary
        self.print_test_summary(results)
        
    def test_guest_game_logging(self):
        """Test if guest games are logged in session."""
        try:
            # Start a new guest session
            self.session.get(f"{self.base_url}/dashboard")
            
            # Start a game
            game_response = self.session.get(f"{self.base_url}/game/simple/easy")
            if game_response.status_code != 200:
                return {"status": "FAIL", "error": "Could not start game"}
            
            # Extract session ID from the response
            session_id = self.extract_session_id_from_response(game_response.text)
            if not session_id:
                return {"status": "FAIL", "error": "Could not extract session ID"}
            
            # Simulate a complete game
            game_result = self.simulate_complete_game(session_id, "easy")
            
            # Check if game appears in dashboard
            dashboard_response = self.session.get(f"{self.base_url}/dashboard")
            if "Recent Games" in dashboard_response.text and "Easy AI" in dashboard_response.text:
                return {"status": "PASS", "details": f"Game logged successfully: {game_result}"}
            else:
                return {"status": "FAIL", "error": "Game not visible in dashboard"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def test_user_registration(self):
        """Test new user registration process."""
        try:
            # Generate unique username
            timestamp = int(time.time())
            username = f"testuser_{timestamp}"
            password = "TestPass123"
            
            # Attempt registration
            reg_data = {
                "username": username,
                "password": password,
                "confirm_password": password
            }
            
            reg_response = self.session.post(
                f"{self.base_url}/auth/register",
                data=reg_data,
                allow_redirects=False
            )
            
            if reg_response.status_code in [302, 200]:  # Redirect or success
                # Try to access dashboard (should be logged in)
                dashboard_response = self.session.get(f"{self.base_url}/dashboard")
                if dashboard_response.status_code == 200:
                    return {"status": "PASS", "details": f"User {username} created and logged in"}
                else:
                    return {"status": "FAIL", "error": "Registration succeeded but not logged in"}
            else:
                return {"status": "FAIL", "error": f"Registration failed: {reg_response.status_code}"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def test_logged_user_game_logging(self):
        """Test if logged-in user games are saved to database."""
        try:
            # Should already be logged in from previous test
            # Start a game
            game_response = self.session.get(f"{self.base_url}/game/simple/medium")
            if game_response.status_code != 200:
                return {"status": "FAIL", "error": "Could not start game as logged user"}
            
            session_id = self.extract_session_id_from_response(game_response.text)
            if not session_id:
                return {"status": "FAIL", "error": "Could not extract session ID"}
            
            # Simulate a complete game
            game_result = self.simulate_complete_game(session_id, "medium")
            
            # Check statistics page
            stats_response = self.session.get(f"{self.base_url}/statistics")
            if stats_response.status_code == 200 and "Total Games" in stats_response.text:
                return {"status": "PASS", "details": f"Logged user game recorded: {game_result}"}
            else:
                return {"status": "FAIL", "error": "Stats page not accessible or empty"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def test_database_tables(self):
        """Test if database tables are created properly for new users."""
        try:
            # This is indirectly tested by checking if stats page works
            stats_response = self.session.get(f"{self.base_url}/statistics")
            
            if stats_response.status_code == 200:
                # Check if the page has the expected structure
                if all(keyword in stats_response.text for keyword in 
                       ["Total Games", "Victories", "Win Rate", "Easy AI", "Medium AI", "Hard AI"]):
                    return {"status": "PASS", "details": "Database tables working correctly"}
                else:
                    return {"status": "FAIL", "error": "Stats page missing expected elements"}
            else:
                return {"status": "FAIL", "error": f"Stats page not accessible: {stats_response.status_code}"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def test_stats_accuracy(self):
        """Test if stats are calculated and displayed accurately."""
        try:
            # Play multiple games and verify stats
            games_played = 0
            games_won = 0
            
            for i in range(3):  # Play 3 quick games
                game_response = self.session.get(f"{self.base_url}/game/simple/easy")
                session_id = self.extract_session_id_from_response(game_response.text)
                
                if session_id:
                    result = self.simulate_complete_game(session_id, "easy")
                    games_played += 1
                    if result == "player_won":
                        games_won += 1
            
            # Check stats page
            stats_response = self.session.get(f"{self.base_url}/statistics")
            
            # Note: This is a simplified check - in practice you'd parse the HTML to extract exact numbers
            if stats_response.status_code == 200 and str(games_played) in stats_response.text:
                return {"status": "PASS", "details": f"Played {games_played} games, won {games_won}"}
            else:
                return {"status": "PARTIAL", "details": "Stats page accessible but accuracy needs manual verification"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def test_game_completion(self):
        """Test if games can be completed without hanging."""
        try:
            completed_games = 0
            
            for difficulty in ["easy", "medium", "hard"]:
                game_response = self.session.get(f"{self.base_url}/game/simple/{difficulty}")
                session_id = self.extract_session_id_from_response(game_response.text)
                
                if session_id:
                    result = self.simulate_complete_game(session_id, difficulty, max_moves=30)
                    if result in ["player_won", "ai_won", "draw"]:
                        completed_games += 1
            
            if completed_games == 3:
                return {"status": "PASS", "details": "All difficulty levels can complete games"}
            else:
                return {"status": "PARTIAL", "details": f"Only {completed_games}/3 difficulties completed successfully"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def test_ai_difficulty(self):
        """Test if hard AI is actually harder than medium AI."""
        try:
            results = {"medium": [], "hard": []}
            
            # Play multiple games against each difficulty
            for difficulty in ["medium", "hard"]:
                for i in range(5):  # 5 games each
                    game_response = self.session.get(f"{self.base_url}/game/simple/{difficulty}")
                    session_id = self.extract_session_id_from_response(game_response.text)
                    
                    if session_id:
                        result = self.simulate_complete_game(session_id, difficulty, max_moves=40)
                        results[difficulty].append(result)
            
            # Analyze results
            medium_wins = results["medium"].count("ai_won")
            hard_wins = results["hard"].count("ai_won")
            
            if hard_wins >= medium_wins:
                return {"status": "PASS", "details": f"Hard AI won {hard_wins}/5, Medium AI won {medium_wins}/5"}
            else:
                return {"status": "FAIL", "details": f"Hard AI ({hard_wins} wins) not harder than Medium AI ({medium_wins} wins)"}
                
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def extract_session_id_from_response(self, html_content):
        """Extract session ID from the game page HTML."""
        try:
            # Look for the session ID in the JavaScript
            start_marker = "sessionId = '"
            end_marker = "';"
            
            start_index = html_content.find(start_marker)
            if start_index == -1:
                return None
            
            start_index += len(start_marker)
            end_index = html_content.find(end_marker, start_index)
            
            if end_index == -1:
                return None
            
            return html_content[start_index:end_index]
        except:
            return None
    
    def simulate_complete_game(self, session_id, difficulty, max_moves=50):
        """Simulate a complete game by making random valid moves."""
        try:
            move_count = 0
            
            while move_count < max_moves:
                # Get game state
                state_response = self.session.get(f"{self.base_url}/game/api/state/{session_id}")
                if state_response.status_code != 200:
                    return "error"
                
                state = state_response.json()
                
                # Check if game is over
                if state.get('game_over') or state.get('winner') is not None:
                    if state.get('winner') == 1:
                        return "player_won"
                    elif state.get('winner') == -1:
                        return "ai_won"
                    else:
                        return "draw"
                
                # Make a random valid move if it's player's turn
                legal_moves = state.get('legal_moves', [])
                if legal_moves and state.get('current_player') == 1:
                    move = random.choice(legal_moves)
                    
                    move_response = self.session.post(
                        f"{self.base_url}/game/api/move/{session_id}",
                        json={"row": move[0], "col": move[1]}
                    )
                    
                    if move_response.status_code == 200:
                        move_data = move_response.json()
                        
                        # Check if game ended after player move
                        if move_data.get('game_over') or move_data.get('winner') is not None:
                            if move_data.get('winner') == 1:
                                return "player_won"
                            elif move_data.get('winner') == -1:
                                return "ai_won"
                            else:
                                return "draw"
                        
                        # If game continues, trigger AI move
                        if not move_data.get('game_over'):
                            ai_response = self.session.post(f"{self.base_url}/game/api/ai_move/{session_id}")
                            
                            if ai_response.status_code == 200:
                                ai_data = ai_response.json()
                                
                                # Check if AI won
                                if ai_data.get('game_over') or ai_data.get('winner') is not None:
                                    if ai_data.get('winner') == 1:
                                        return "player_won"
                                    elif ai_data.get('winner') == -1:
                                        return "ai_won"
                                    else:
                                        return "draw"
                
                move_count += 1
                time.sleep(0.1)  # Small delay to avoid overwhelming the server
            
            return "timeout"
            
        except Exception as e:
            return f"error: {str(e)}"
    
    def print_test_summary(self, results):
        """Print a formatted summary of all test results."""
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 50)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r['status'] == 'PASS')
        
        for test_name, result in results.items():
            status_emoji = {
                'PASS': '✅',
                'FAIL': '❌', 
                'PARTIAL': '⚠️'
            }.get(result['status'], '❓')
            
            print(f"{status_emoji} {test_name.replace('_', ' ').title()}: {result['status']}")
            if 'details' in result:
                print(f"   └─ {result['details']}")
            if 'error' in result:
                print(f"   └─ Error: {result['error']}")
        
        print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 All systems working perfectly!")
        elif passed_tests >= total_tests * 0.7:
            print("👍 Most systems working well, minor issues to address")
        else:
            print("⚠️ Several issues found, need debugging")

if __name__ == "__main__":
    # Check if server is running
    try:
        requests.get("http://localhost:5000", timeout=5)
        print("✅ Server is running, starting tests...")
    except:
        print("❌ Server not running! Please start with 'python run.py' first")
        exit(1)
    
    # Run all tests
    tester = GameSystemTester()
    tester.test_all()
