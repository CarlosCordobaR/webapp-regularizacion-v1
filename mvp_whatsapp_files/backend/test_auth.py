#!/usr/bin/env python3
"""Test Supabase Auth - Verificar usuario y configuración"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from app.core.config import get_settings

def test_auth():
    settings = get_settings()
    
    # Create Supabase admin client
    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key  # Service role para operaciones admin
    )
    
    print("🔐 Testing Supabase Auth Configuration")
    print("=" * 60)
    print(f"URL: {settings.supabase_url}")
    print(f"Project: {settings.supabase_url.split('//')[1].split('.')[0]}")
    print()
    
    try:
        # Try to list users (requires service_role key)
        response = supabase.auth.admin.list_users()
        users = response
        
        print(f"✅ Found {len(users)} users in Auth")
        print()
        
        for user in users:
            email = user.email
            created = user.created_at
            confirmed = user.email_confirmed_at is not None
            status = "✅ Confirmed" if confirmed else "⚠️ Pending email confirmation"
            
            print(f"  📧 {email}")
            print(f"     ID: {user.id}")
            print(f"     Status: {status}")
            print(f"     Created: {created}")
            print()
            
            if email == "carlosm@mail.com":
                print("  🎯 Found carlosm@mail.com!")
                if not confirmed:
                    print("  ⚠️  This user needs to confirm their email before logging in.")
                    print("  💡 Options:")
                    print("     1. Check spam folder for confirmation email")
                    print("     2. Manually confirm in Supabase Dashboard > Authentication > Users")
                    print("     3. Disable email confirmation in Supabase Dashboard > Authentication > Providers > Email")
                else:
                    print("  ✅ User is confirmed and ready to login!")
                print()
        
        if not users:
            print("⚠️  No users found in Supabase Auth")
            print("💡 The user might have been created in a different way")
            print("   or email confirmation is pending.")
        
    except Exception as e:
        print(f"❌ Error accessing Supabase Auth: {e}")
        print()
        print("💡 Make sure:")
        print("   1. SUPABASE_SERVICE_ROLE_KEY is set correctly")
        print("   2. Auth service is enabled in Supabase")
        return False
    
    print()
    print("📋 Next steps:")
    print("   1. If user needs confirmation: Check email or manually confirm in dashboard")
    print("   2. Try login at: http://localhost:5173/login")
    print("   3. Use email: carlosm@mail.com")
    print()
    
    return True

if __name__ == "__main__":
    test_auth()
