#!/usr/bin/env python3
"""
Database Migration Runner
Executes SQL migrations against Supabase database
"""
import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

def get_supabase_client() -> Client:
    """Create Supabase client with service role key"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    
    return create_client(url, key)

def run_migration(client: Client, migration_file: Path) -> bool:
    """Execute a migration file"""
    print(f"\n{'='*60}")
    print(f"Running migration: {migration_file.name}")
    print(f"{'='*60}")
    
    try:
        # Read migration SQL
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Remove comments and split into statements
        statements = []
        for line in sql.split('\n'):
            # Skip comment lines and empty lines
            line = line.strip()
            if line and not line.startswith('--'):
                statements.append(line)
        
        sql_clean = ' '.join(statements)
        
        # Execute using Supabase RPC (raw SQL execution)
        # Note: Supabase Python client doesn't have direct SQL execution
        # We need to use the PostgREST API or psycopg2
        
        print(f"📝 SQL to execute:")
        print(sql)
        
        # Use supabase.postgrest to execute raw SQL via RPC
        # This requires creating a custom RPC function in Supabase
        # Alternative: Use psycopg2 for direct SQL execution
        
        print(f"⚠️  Supabase Python client doesn't support raw SQL execution directly.")
        print(f"Using alternative method with psycopg2...")
        
        # Import psycopg2 for direct database connection
        import psycopg2
        
        # Extract database connection string from SUPABASE_URL
        supabase_url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # For Supabase, we need to construct the PostgreSQL connection string
        # Format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
        project_ref = supabase_url.split('//')[1].split('.')[0]
        
        print(f"⚠️  To run migrations, you need the database password.")
        print(f"Please run migrations using one of these methods:")
        print(f"\n1. Supabase Dashboard SQL Editor:")
        print(f"   - Go to: https://supabase.com/dashboard/project/{project_ref}/sql")
        print(f"   - Copy and paste the SQL from: {migration_file}")
        print(f"\n2. Supabase CLI:")
        print(f"   - supabase db push --db-url [your-connection-string]")
        print(f"\n3. SQL printed above - execute manually")
        
        return False
        
    except Exception as e:
        print(f"❌ Error executing migration: {e}")
        return False

def main():
    """Run all pending migrations"""
    print("🚀 Starting database migrations...")
    
    # Get migrations directory
    migrations_dir = Path(__file__).parent / "app" / "db" / "migrations"
    
    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    # Get all .sql files sorted by name
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print(f"ℹ️  No migration files found in {migrations_dir}")
        sys.exit(0)
    
    print(f"Found {len(migration_files)} migration(s)")
    
    # Create Supabase client
    try:
        client = get_supabase_client()
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        sys.exit(1)
    
    # Run each migration
    success_count = 0
    for migration_file in migration_files:
        if run_migration(client, migration_file):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"Migration Summary: {success_count}/{len(migration_files)} succeeded")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
