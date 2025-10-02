#!/usr/bin/env python3
"""
Create User Script for Intelligence Platform
===========================================
This script creates a new user in the PostgreSQL database
"""

import sys
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app components
from app1_production import app, db, User

def create_user(username, password, role='user', is_active=True):
    """
    Create a new user in the database
    
    Args:
        username (str): Username for the new user
        password (str): Plain text password (will be hashed)
        role (str): User role ('admin' or 'user')
        is_active (bool): Whether the user is active
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with app.app_context():
            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"❌ User '{username}' already exists")
                return False
            
            # Create new user
            new_user = User(
                username=username,
                password=generate_password_hash(password),
                role=role,
                created_at=datetime.utcnow(),
                is_active=is_active
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"✅ User '{username}' created successfully")
            print(f"   Role: {role}")
            print(f"   Active: {is_active}")
            print(f"   Created: {new_user.created_at}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        if db.session:
            db.session.rollback()
        return False

def list_users():
    """List all users in the database"""
    try:
        with app.app_context():
            users = User.query.order_by(User.created_at.desc()).all()
            
            print(f"\n📊 Current Users ({len(users)} total):")
            print("-" * 80)
            for user in users:
                status = "✅ Active" if user.is_active else "❌ Inactive"
                last_login = user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "Never"
                print(f"ID: {user.id:2d} | {user.username:20s} | {user.role:5s} | {status} | Last: {last_login}")
            
    except Exception as e:
        print(f"❌ Error listing users: {e}")

def main():
    """Main function to handle user creation"""
    print("=" * 60)
    print("INTELLIGENCE PLATFORM - USER CREATION TOOL")
    print("=" * 60)
    
    if len(sys.argv) == 1:
        print("Usage:")
        print(f"  {sys.argv[0]} list                              # List all users")
        print(f"  {sys.argv[0]} create <username> <password>      # Create regular user")
        print(f"  {sys.argv[0]} create <username> <password> admin # Create admin user")
        print()
        print("Examples:")
        print(f"  {sys.argv[0]} create john.doe password123")
        print(f"  {sys.argv[0]} create admin.user SecurePass123! admin")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_users()
    
    elif command == "create":
        if len(sys.argv) < 4:
            print("❌ Error: Username and password required")
            print(f"Usage: {sys.argv[0]} create <username> <password> [role]")
            return
        
        username = sys.argv[2]
        password = sys.argv[3]
        role = sys.argv[4] if len(sys.argv) > 4 else 'user'
        
        if role not in ['user', 'admin']:
            print("❌ Error: Role must be 'user' or 'admin'")
            return
        
        print(f"Creating user: {username}")
        print(f"Role: {role}")
        
        if create_user(username, password, role):
            print(f"\n🎉 User creation successful!")
            print(f"   Login at: https://localhost")
            print(f"   Username: {username}")
            print(f"   Role: {role}")
        else:
            print(f"💥 User creation failed")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: list, create")

if __name__ == "__main__":
    main()
