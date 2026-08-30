"""
Add a new individual admin user.

Run this once per person you want to give admin access to.
Their password is hashed before being stored - never saved
as plain text.

Run from the project root:
  .venv\\Scripts\\python.exe add_admin_user.py
"""

import sys
import os
import getpass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.database import add_admin_user, get_admin_user_by_username

print("=" * 50)
print("Add New Admin User")
print("=" * 50)

name = input("Full name (e.g. Ravi Kumar): ").strip()
username = input("Username (they'll log in with this): ").strip()

existing = get_admin_user_by_username(username)

if existing:
    print(f"\n❌ Username '{username}' already exists. Choose a different one.")
    sys.exit(1)

password = getpass.getpass("Password (hidden while typing): ").strip()
confirm_password = getpass.getpass("Confirm password: ").strip()

if not name or not username or not password:
    print("\n❌ Name, username, and password cannot be empty.")
    sys.exit(1)

if password != confirm_password:
    print("\n❌ Passwords don't match. Please try again.")
    sys.exit(1)

if len(password) < 8:
    print("\n⚠️  Warning: that's a fairly short password. Consider using something longer.")

add_admin_user(name, username, password)

print(f"\n✅ Admin account created for {name} (username: {username}).")
print("They can now log in at /admin/ with these credentials.")