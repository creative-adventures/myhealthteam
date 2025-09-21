import sqlite3

DB_PATH = 'production.db'

def add_admin_role():
    conn = sqlite3.connect(DB_PATH)
    try:
        # Assuming user_id 1 is the admin user and role_id 41 is the Admin role
        conn.execute("INSERT INTO user_roles (user_id, role_id, is_primary) VALUES (?, ?, ?)", (1, 41, 1))
        conn.commit()
        print("Admin role added to user 1.")
    except sqlite3.IntegrityError:
        print("User 1 already has the Admin role.")
    finally:
        conn.close()

if __name__ == '__main__':
    add_admin_role()