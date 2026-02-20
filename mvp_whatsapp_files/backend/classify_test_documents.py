#!/usr/bin/env python3
"""
Classify existing documents with document_type for testing
"""
import os
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

def classify_documents():
    """Classify existing documents for the test client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    client = create_client(url, key)
    
    test_client_id = "d78f4683-a2c4-408a-aee6-bc6be6b1df79"
    
    print("📄 Clasificando documentos del cliente de prueba...\n")
    
    # Get documents
    response = client.table("documents").select("*").eq("client_id", test_client_id).execute()
    docs = response.data
    
    print(f"Encontrados {len(docs)} documentos\n")
    
    if len(docs) >= 2:
        # Classify first as TASA
        doc1 = docs[0]
        result1 = client.table("documents").update({
            "document_type": "TASA"
        }).eq("id", doc1["id"]).execute()
        print(f"✅ {doc1['original_filename']} → TASA")
        
        # Classify second as PASSPORT_NIE
        doc2 = docs[1]
        result2 = client.table("documents").update({
            "document_type": "PASSPORT_NIE"
        }).eq("id", doc2["id"]).execute()
        print(f"✅ {doc2['original_filename']} → PASSPORT_NIE")
        
        print("\n" + "="*60)
        print("✅ Documentos clasificados correctamente")
        print("="*60)
        print("\n🎯 Ahora puedes probar la funcionalidad 'Generar expediente'")
    else:
        print("⚠️  Cliente necesita al menos 2 documentos")
        print("   Sube documentos desde el frontend primero")

if __name__ == "__main__":
    classify_documents()
