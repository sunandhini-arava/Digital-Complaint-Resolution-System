"""
Run this once after setup_database.sql to set the real super admin password.
Usage: python seed_admin.py
"""
import bcrypt
import pymysql
import getpass
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from config import Config

def seed_admin():
    print("=" * 50)
    print("  CMS - Super Admin Password Setup")
    print("=" * 50)
    password = getpass.getpass("Enter super admin password (min 8 chars): ")
    if len(password) < 8:
        print("Password too short.")
        sys.exit(1)
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = pymysql.connect(
        host=Config.MYSQL_HOST, user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD, database=Config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password=%s, is_activated=TRUE WHERE user_id='ADMIN001'",
                (hashed,)
            )
            if cursor.rowcount == 0:
                # Insert fresh
                cursor.execute(
                    """INSERT INTO users (user_id, password, full_name, email, phone, user_type, birthdate, is_activated)
                       VALUES ('ADMIN001',%s,'Sunandhini','admin@institution.edu','9999999999','admin','1990-01-01',TRUE)
                       ON DUPLICATE KEY UPDATE password=%s, is_activated=TRUE""",
                    (hashed, hashed)
                )
        conn.commit()
        print("\n✅ Super admin password set successfully.")
        print("   User ID: ADMIN001")
        print("   Login at /login.html")
    finally:
        conn.close()

if __name__ == '__main__':
    seed_admin()
