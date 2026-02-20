#!/usr/bin/env python3
"""Confirmar usuario en Supabase Auth"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from app.core.config import get_settings

def confirm_user(email: str):
    settings = get_settings()
    
    # Create Supabase admin client
    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )
    
    print(f"🔐 Confirming user: {email}")
    print("=" * 60)
    
    try:
        # Get user by email
        response = supabase.auth.admin.list_users()
        users = response
        
        user = None
        for u in users:
            if u.email == email:
                user = u
                break
        
        if not user:
            print(f"❌ User {email} not found")
            return False
        
        print(f"✅ Found user: {user.id}")
        
        if user.email_confirmed_at:
            print(f"ℹ️  User already confirmed at {user.email_confirmed_at}")
            print(f"✅ User can login now!")
            return True
        
        # Update user to confirm email
        print("📧 Confirming email...")
        supabase.auth.admin.update_user_by_id(
            user.id,
            {"email_confirm": True}
        )
        
        print(f"✅ Email confirmed for {email}!")
        print()
        print("🎉 User is now ready to login!")
        print(f"   URL: http://localhost:5173/login")
        print(f"   Email: {email}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        email = "carlosm@mail.com"
    
    confirm_user(email)
