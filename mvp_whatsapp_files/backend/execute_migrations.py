#!/usr/bin/env python3
"""
Execute database migrations using Supabase Management API
"""
import os
import sys
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

def execute_sql_via_api(sql: str, project_ref: str, service_key: str) -> dict:
    """Execute SQL using Supabase Management API"""
    # Extract project ref from URL
    url = f"https://{project_ref}.supabase.co/rest/v1/rpc/exec_sql"
    
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": sql
    }
    
    response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    return response

def run_migrations():
    """Execute all migrations"""
    print("🚀 Running database migrations...\n")
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not service_key:
        print("❌ SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)
    
    # Extract project reference
    project_ref = supabase_url.split("//")[1].split(".")[0]
    
    # Read migration files
    migrations_dir = Path(__file__).parent / "app" / "db" / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("ℹ️  No migration files found")
        return
    
    print(f"Found {len(migration_files)} migration(s)\n")
    
    # Execute each migration
    for migration_file in migration_files:
        print(f"{'='*70}")
        print(f"📝 Migration: {migration_file.name}")
        print(f"{'='*70}\n")
        
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        print("SQL to execute:")
        print(sql)
        print()
        
        # Since Supabase doesn't expose a direct SQL execution endpoint,
        # we need to use the SQL Editor or provide manual instructions
        print("⚠️  Automatic execution not available via Supabase API")
        print("Please execute this SQL manually using one of these methods:\n")
        print(f"1. 🌐 Supabase Dashboard SQL Editor:")
        print(f"   https://supabase.com/dashboard/project/{project_ref}/sql/new")
        print(f"\n2. 📋 Copy the SQL above and paste it in the editor")
        print(f"\n3. ▶️  Click 'Run' to execute\n")
    
    # Create a consolidated migration file for convenience
    consolidated_file = Path(__file__).parent / "migrations_consolidated.sql"
    with open(consolidated_file, 'w') as f:
        f.write("-- Consolidated migrations for expediente feature\n")
        f.write(f"-- Generated: {Path.cwd()}\n")
        f.write("-- Execute this entire file in Supabase SQL Editor\n\n")
        
        for migration_file in migration_files:
            with open(migration_file, 'r') as mf:
                f.write(f"\n-- {'='*60}\n")
                f.write(f"-- {migration_file.name}\n")
                f.write(f"-- {'='*60}\n\n")
                f.write(mf.read())
                f.write("\n\n")
    
    print(f"{'='*70}")
    print(f"✅ Consolidated migration file created:")
    print(f"   {consolidated_file}")
    print(f"{'='*70}\n")
    print("📋 You can copy this file's content and paste it into Supabase SQL Editor\n")

if __name__ == "__main__":
    run_migrations()
