"""
Create Supabase Auth Users

Creates 5 test users in Supabase Auth for development purposes.
Idempotent: Skips users that already exist.

Usage:
    python -m app.scripts.create_supabase_users

Environment variables required:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY

WARNING: Hardcoded credentials are for DEV/TEST only!
In production, use proper user management workflows.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.logging import get_logger
from app.db.supabase import get_supabase_client

logger = get_logger(__name__)


# DEV USERS - DO NOT USE IN PRODUCTION
TEST_USERS = [
    {
        "email": "admin@local.test",
        "password": "Admin123!",
        "name": "Admin User",
        "role": "admin",
    },
    {
        "email": "ops1@local.test",
        "password": "Ops123!",
        "name": "Operations Manager 1",
        "role": "operations",
    },
    {
        "email": "ops2@local.test",
        "password": "Ops123!",
        "name": "Operations Manager 2",
        "role": "operations",
    },
    {
        "email": "reviewer@local.test",
        "password": "Review123!",
        "name": "Content Reviewer",
        "role": "reviewer",
    },
    {
        "email": "readonly@local.test",
        "password": "Read123!",
        "name": "Read Only User",
        "role": "readonly",
    },
]


def create_user_via_admin_api(supabase_client, user_data: Dict[str, Any]) -> bool:
    """
    Create user using Supabase Admin API.
    
    Returns:
        True if user was created, False if already exists or error
    """
    email = user_data["email"]
    password = user_data["password"]
    metadata = {
        "name": user_data.get("name", ""),
        "role": user_data.get("role", "user"),
    }
    
    try:
        # Use admin API to create user
        response = supabase_client.client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # Auto-confirm email for dev
            "user_metadata": metadata
        })
        
        if response:
            logger.info(f"✓ Created user: {email} ({metadata['name']}) - Role: {metadata['role']}")
            return True
        else:
            logger.warning(f"✗ Failed to create user: {email}")
            return False
            
    except Exception as e:
        error_str = str(e).lower()
        
        # Check if user already exists
        if "already" in error_str or "exists" in error_str or "duplicate" in error_str:
            logger.info(f"⊙ User already exists: {email}")
            return False
        
        # Other error
        logger.error(f"✗ Error creating user {email}: {e}")
        return False


def list_existing_users(supabase_client) -> List[str]:
    """List existing user emails in Supabase Auth."""
    try:
        # Try to list users (may require admin privileges)
        response = supabase_client.client.auth.admin.list_users()
        
        if response and hasattr(response, 'users'):
            emails = [user.email for user in response.users if user.email]
            logger.info(f"Found {len(emails)} existing users")
            return emails
        return []
    except Exception as e:
        logger.debug(f"Could not list existing users: {e}")
        return []


def main():
    """Main function to create test users."""
    logger.info("=" * 80)
    logger.info("Creating Supabase Auth Test Users")
    logger.info("=" * 80)
    
    # Check environment variables
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file or export them before running this script")
        sys.exit(1)
    
    # Initialize Supabase client
    try:
        supabase_client = get_supabase_client()
        logger.info(f"Connected to Supabase: {os.getenv('SUPABASE_URL')}")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        sys.exit(1)
    
    # Try to list existing users
    existing_emails = list_existing_users(supabase_client)
    
    # Create users
    created_count = 0
    skipped_count = 0
    failed_count = 0
    
    logger.info("")
    logger.info(f"Creating {len(TEST_USERS)} test users...")
    logger.info("")
    
    for user_data in TEST_USERS:
        email = user_data["email"]
        
        # Skip if already exists (from pre-check)
        if email in existing_emails:
            logger.info(f"⊙ User already exists: {email}")
            skipped_count += 1
            continue
        
        # Try to create
        result = create_user_via_admin_api(supabase_client, user_data)
        
        if result:
            created_count += 1
        else:
            # Could be existing or failed
            if email not in existing_emails:
                failed_count += 1
            else:
                skipped_count += 1
    
    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✓ Created:  {created_count}")
    logger.info(f"⊙ Skipped:  {skipped_count} (already exist)")
    logger.info(f"✗ Failed:   {failed_count}")
    logger.info("")
    
    if created_count > 0 or skipped_count == len(TEST_USERS):
        logger.info("✓ All test users are available in Supabase")
        logger.info("")
        logger.info("TEST CREDENTIALS (DEV ONLY):")
        logger.info("-" * 80)
        for user in TEST_USERS:
            logger.info(f"  {user['email']:<25} | {user['password']:<15} | {user['role']:<15}")
        logger.info("-" * 80)
        logger.info("")
        logger.info("⚠️  WARNING: These are hardcoded test credentials!")
        logger.info("   DO NOT use in production. Implement proper user management.")
    else:
        logger.error("Some users could not be created. Check logs above.")
        sys.exit(1)
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
