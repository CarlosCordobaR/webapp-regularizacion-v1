#!/usr/bin/env python3
"""
Clasificar documentos de Juan Juan manualmente
"""
import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://awfvttwdvqnxhgiwxkpp.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF3ZnZ0dHdkdnFueGhnaXd4a3BwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NDQ4NDE5OSwiZXhwIjoyMDYwMDYwMTk5fQ.d9N7yB3jcmHM9LSthc5wI9F3hcmhYTZEpKHpqOGo9M4")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CLIENT_ID = "62d38f0b-0648-4c8a-a3de-6f4778c585e5"

print("🔍 Obteniendo documentos de Juan Juan...")
response = supabase.table('documents').select('*').eq('client_id', CLIENT_ID).execute()
docs = response.data

print(f"\n📄 Encontrados {len(docs)} documentos:")
for i, doc in enumerate(docs, 1):
    print(f"  {i}. {doc['original_filename']} (ID: {doc['id'][:8]}...)")
    print(f"     Tipo actual: {doc.get('document_type', 'None')}")

print("\n✅ Clasificando documentos...")

# Clasificar cada documento según su nombre
for doc in docs:
    filename = doc['original_filename'].lower()
    
    if 'tasa' in filename:
        doc_type = 'TASA'
    elif 'pasaporte' in filename or 'passport' in filename:
        doc_type = 'PASSPORT_NIE'
    else:
        doc_type = None
    
    if doc_type:
        print(f"  ✓ {doc['original_filename']} → {doc_type}")
        supabase.table('documents').update({
            'document_type': doc_type
        }).eq('id', doc['id']).execute()
    else:
        print(f"  ⚠️ {doc['original_filename']} → No se pudo determinar tipo automáticamente")

print("\n✅ Clasificación completada!")
print("\n🧪 Verificando...")

response = supabase.table('documents').select('*').eq('client_id', CLIENT_ID).execute()
docs = response.data

print(f"\n📊 Estado final:")
for doc in docs:
    status = "✅" if doc.get('document_type') else "❌"
    print(f"  {status} {doc['original_filename']}: {doc.get('document_type', 'None')}")

has_tasa = any(d.get('document_type') == 'TASA' for d in docs)
has_passport = any(d.get('document_type') == 'PASSPORT_NIE' for d in docs)

print(f"\n{'✅' if has_tasa else '❌'} Tiene TASA")
print(f"{'✅' if has_passport else '❌'} Tiene PASSPORT_NIE")

if has_tasa and has_passport:
    print("\n🎉 ¡Juan Juan ahora puede generar expediente!")
else:
    print("\n⚠️ Faltan documentos requeridos para expediente")
