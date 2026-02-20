#!/usr/bin/env python3
"""
Update existing clients with passport_or_nie values
"""
import os
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

def update_clients():
    """Update clients with sample passport/NIE values"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    client = create_client(url, key)
    
    print("🔄 Actualizando clientes existentes...\n")
    
    # Get all clients
    response = client.table("clients").select("id, phone_number, name, passport_or_nie").execute()
    clients = response.data
    
    print(f"📊 Encontrados {len(clients)} clientes")
    print()
    
    # Sample NIE/Passport values for testing
    # Spanish NIE format: X1234567A or Y1234567B or Z1234567C
    sample_nies = [
        "X1234567A",  # NIE español
        "Y7654321B",  # NIE español
        "Z9876543C",  # NIE español
        "12345678A",  # DNI español
        "AB123456",   # Pasaporte
        "CD789012",   # Pasaporte
        "EF345678",   # Pasaporte
        "X2468135A",  # NIE español
        "Y1357924B",  # NIE español
        "Z8642097C",  # NIE español
    ]
    
    # Update known test client first
    test_client_id = "d78f4683-a2c4-408a-aee6-bc6be6b1df79"
    test_client = next((c for c in clients if c['id'] == test_client_id), None)
    
    if test_client:
        print(f"🎯 Actualizando cliente de prueba conocido:")
        print(f"   ID: {test_client_id}")
        print(f"   Nombre: {test_client.get('name', 'Sin nombre')}")
        print(f"   Teléfono: {test_client.get('phone_number')}")
        
        result = client.table("clients").update({
            "passport_or_nie": "X1234567A"  # NIE español para detección
        }).eq("id", test_client_id).execute()
        
        print(f"   ✅ Actualizado con NIE: X1234567A")
        print()
    
    # Update remaining clients with sample values
    print("📝 Actualizando el resto de clientes con valores de prueba...")
    updated_count = 0
    
    for idx, client_data in enumerate(clients):
        if client_data['id'] == test_client_id:
            continue  # Skip test client (already updated)
        
        if client_data['passport_or_nie'] == 'PENDING':
            # Use sample values in rotation
            sample_value = sample_nies[idx % len(sample_nies)]
            
            client.table("clients").update({
                "passport_or_nie": sample_value
            }).eq("id", client_data['id']).execute()
            
            updated_count += 1
            
            if updated_count <= 5:  # Show first 5
                print(f"   ✅ {client_data.get('name', 'Sin nombre')}: {sample_value}")
    
    if updated_count > 5:
        print(f"   ... y {updated_count - 5} más")
    
    print()
    print("=" * 60)
    print(f"✅ Actualización completada: {updated_count + 1} clientes")
    print("=" * 60)
    print()
    
    # Verify
    print("🔍 Verificando actualización...")
    response = client.table("clients").select("id, name, passport_or_nie").execute()
    
    pending = [c for c in response.data if c.get('passport_or_nie') == 'PENDING']
    print(f"   Clientes con 'PENDING': {len(pending)}")
    
    if len(pending) == 0:
        print("   ✅ Todos los clientes actualizados correctamente")
    else:
        print(f"   ⚠️  Quedan {len(pending)} clientes por actualizar")

if __name__ == "__main__":
    update_clients()
