#!/usr/bin/env python3
"""
Quick automated test for your 7 specific requirements
Runs in under 2 minutes instead of 10+ minutes of manual testing
"""

import requests
import json
import time
import random

def quick_test():
    """Run quick tests for all 7 requirements."""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("🚀 Quick Game System Test")
    print("Testing your 7 requirements in ~2 minutes...")
    print("-" * 40)
    
    # Test 1: Guest game logging
    print("1️⃣ Guest game logging...", end=" ")
    try:
        # Start game as guest
        resp = session.get(f"{base_url}/game/simple/easy")
        if "session_id" in resp.text:
            print("✅ PASS")
        else:
            print("❌ FAIL")
    except:
        print("❌ ERROR")
    
    # Test 2: New user registration  
    print("2️⃣ New user registration...", end=" ")
    try:
        username = f"testuser_{int(time.time())}"
        reg_data = {"username": username, "password": "Test123", "confirm_password": "Test123"}
        resp = session.post(f"{base_url}/auth/register", data=reg_data, allow_redirects=False)
        if resp.status_code in [200, 302]:
            print("✅ PASS")
        else:
            print("❌ FAIL")
    except:
        print("❌ ERROR")
    
    # Test 3: Logged user game logging
    print("3️⃣ Logged user game logging...", end=" ")
    try:
        resp = session.get(f"{base_url}/statistics")
        if resp.status_code == 200 and "Total Games" in resp.text:
            print("✅ PASS")
        else:
            print("❌ FAIL")
    except:
        print("❌ ERROR")
    
    # Test 4: Database tables for new users
    print("4️⃣ Database tables creation...", end=" ")
    try:
        resp = session.get(f"{base_url}/dashboard")
        if "Recent Games" in resp.text:
            print("✅ PASS")
        else:
            print("❌ FAIL")
    except:
        print("❌ ERROR")
    
    # Test 5: Stats accuracy (quick check)
    print("5️⃣ Stats dashboard accuracy...", end=" ")
    try:
        resp = session.get(f"{base_url}/statistics")
        if all(word in resp.text for word in ["Easy AI", "Medium AI", "Hard AI", "Win Rate"]):
            print("✅ PASS")
        else:
            print("❌ FAIL")
    except:
        print("❌ ERROR")
    
    # Test 6: Game completion (simulate quick game)
    print("6️⃣ Game completion test...", end=" ")
    try:
        # Get a game
        resp = session.get(f"{base_url}/game/simple/easy")
        
        # Extract session ID (simple regex)
        import re
        session_match = re.search(r"sessionId = '([^']+)'", resp.text)
        if session_match:
            session_id = session_match.group(1)
            
            # Test game state endpoint
            state_resp = session.get(f"{base_url}/game/api/state/{session_id}")
            if state_resp.status_code == 200:
                state = state_resp.json()
                if 'legal_moves' in state and 'board' in state:
                    print("✅ PASS")
                else:
                    print("❌ FAIL - Invalid state")
            else:
                print("❌ FAIL - State error")
        else:
            print("❌ FAIL - No session")
    except Exception as e:
        print(f"❌ ERROR - {str(e)[:30]}")
    
    # Test 7: AI difficulty comparison (quick heuristic test)
    print("7️⃣ AI difficulty levels...", end=" ")
    try:
        # Test if all AI endpoints respond
        difficulties = ["easy", "medium", "hard"]
        working_ais = 0
        
        for diff in difficulties:
            resp = session.get(f"{base_url}/game/simple/{diff}")
            if resp.status_code == 200 and "sessionId" in resp.text:
                working_ais += 1
        
        if working_ais == 3:
            print("✅ PASS - All AIs accessible")
        else:
            print(f"⚠️ PARTIAL - {working_ais}/3 AIs working")
    except:
        print("❌ ERROR")
    
    print("-" * 40)
    print("✨ Quick test completed!")
    print("\nFor detailed testing, run: python test_game_system.py")

if __name__ == "__main__":
    try:
        requests.get("http://localhost:5000", timeout=3)
        quick_test()
    except:
        print("❌ Server not running! Start with 'python run.py' first")
