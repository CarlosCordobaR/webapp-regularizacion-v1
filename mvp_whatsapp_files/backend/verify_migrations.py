#!/usr/bin/env python3
"""
Verify migrations were applied successfully
"""
import os
import sys
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

def verify_migrations():
    """Verify that migrations were applied"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    client = create_client(url, key)
    
    print("🔍 Verificando migraciones...\n")
    
    migrations_ok = True
    
    # Check passport_or_nie column
    try:
        response = client.table("clients").select("id, passport_or_nie").limit(1).execute()
        print("✅ Migración 1: Column 'passport_or_nie' existe")
        if response.data:
            print(f"   Valor de ejemplo: {response.data[0].get('passport_or_nie')}")
    except Exception as e:
        print(f"❌ Migración 1: FALLÓ - {e}")
        migrations_ok = False
    
    print()
    
    # Check document_type column
    try:
        response = client.table("documents").select("id, document_type").limit(1).execute()
        print("✅ Migración 2: Column 'document_type' existe")
        if response.data:
            print(f"   Valor de ejemplo: {response.data[0].get('document_type')}")
    except Exception as e:
        print(f"❌ Migración 2: FALLÓ - {e}")
        migrations_ok = False
    
    print()
    
    if migrations_ok:
        print("=" * 60)
        print("✅ TODAS LAS MIGRACIONES APLICADAS CORRECTAMENTE")
        print("=" * 60)
        print("\n📊 Estado de los datos:")
        
        # Count clients
        clients_response = client.table("clients").select("id, phone_number, name, passport_or_nie").execute()
        print(f"\n   Clientes totales: {len(clients_response.data)}")
        
        # Show clients with PENDING
        pending = [c for c in clients_response.data if c.get('passport_or_nie') == 'PENDING']
        print(f"   Clientes con passport_or_nie='PENDING': {len(pending)}")
        
        if pending:
            print("\n   ⚠️  Necesita actualizar estos clientes:")
            for client in pending[:5]:  # Show first 5
                print(f"      - {client.get('name', 'Sin nombre')} ({client.get('phone_number')})")
            if len(pending) > 5:
                print(f"      ... y {len(pending) - 5} más")
        
        return True
    else:
        print("=" * 60)
        print("❌ ALGUNAS MIGRACIONES FALLARON")
        print("=" * 60)
        print("\nPor favor ejecute el SQL en el Supabase SQL Editor:")
        print("https://supabase.com/dashboard/project/vqcjovttaucekugwmefj/sql/new")
        return False

if __name__ == "__main__":
    success = verify_migrations()
    sys.exit(0 if success else 1)
