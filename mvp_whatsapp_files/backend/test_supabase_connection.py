#!/usr/bin/env python3
"""Test Supabase connection with existing client"""
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

try:
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    
    # Test query
    response = supabase.table('clients').select('id').limit(1).execute()
    print(f'✅ Supabase client funciona correctamente')
    print(f'📊 Respuesta: {len(response.data)} registro(s)')
    
    # Count clients
    response = supabase.table('clients').select('*', count='exact').execute()
    print(f'📊 Total clientes: {response.count}')
    
except Exception as e:
    print(f'❌ Error con Supabase client: {e}')
