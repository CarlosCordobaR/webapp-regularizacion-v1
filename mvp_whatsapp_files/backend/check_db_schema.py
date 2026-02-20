#!/usr/bin/env python3
"""
Check if migrations have been applied
"""
import os
import sys
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

def check_schema():
    """Check if schema has been migrated"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    client = create_client(url, key)
    
    print("🔍 Checking database schema...\n")
    
    # Try to query a client to see if passport_or_nie exists
    try:
        response = client.table("clients").select("id, phone_number, name, passport_or_nie").limit(1).execute()
        print("✅ Column 'passport_or_nie' exists in clients table")
        print(f"   Found {len(response.data)} clients")
        if response.data:
            print(f"   Sample: {response.data[0]}")
    except Exception as e:
        if "column" in str(e).lower() and "passport_or_nie" in str(e).lower():
            print("❌ Column 'passport_or_nie' does NOT exist")
            print("   Migration 001 needs to be applied")
        else:
            print(f"⚠️  Error checking clients: {e}")
    
    print()
    
    # Try to query documents to see if document_type exists
    try:
        response = client.table("documents").select("id, original_filename, document_type").limit(1).execute()
        print("✅ Column 'document_type' exists in documents table")
        print(f"   Found {len(response.data)} documents")
        if response.data:
            print(f"   Sample: {response.data[0]}")
    except Exception as e:
        if "column" in str(e).lower() and "document_type" in str(e).lower():
            print("❌ Column 'document_type' does NOT exist")
            print("   Migration 002 needs to be applied")
        else:
            print(f"⚠️  Error checking documents: {e}")
    
    print()
    
    # Count total clients for migration planning
    try:
        response = client.table("clients").select("id", count="exact").execute()
        print(f"📊 Total clients in database: {response.count}")
    except Exception as e:
        print(f"⚠️  Error counting clients: {e}")

if __name__ == "__main__":
    check_schema()
