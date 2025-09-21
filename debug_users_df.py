#!/usr/bin/env python3
"""
Debug user dataframe structure
"""
import sys
sys.path.append('.')
from src import database as db
import pandas as pd

def debug_users():
    print("=== Debugging User DataFrame Structure ===")
    
    try:
        users = db.get_all_users()
        if users:
            print(f"Number of users: {len(users)}")
            print(f"First user: {users[0]}")
            print(f"User keys: {list(users[0].keys())}")
            
            df = pd.DataFrame(users)
            print(f"DataFrame columns: {list(df.columns)}")
            print(f"DataFrame shape: {df.shape}")
        else:
            print("No users found")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_users()