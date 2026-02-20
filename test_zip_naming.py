#!/usr/bin/env python3
"""
Test script to verify ZIP naming logic
"""
import re

def sanitize_name(name: str) -> str:
    """Sanitize client name for use in filenames."""
    # Replace spaces with underscores
    sanitized = name.replace(" ", "_")
    # Remove special characters
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', sanitized)
    # Convert to lowercase
    sanitized = sanitized.lower()
    return sanitized

# Test cases
test_cases = [
    {
        "name": "Juan Juan",
        "passport": "BC123456",
        "client_id": "62d38f0b-0648-4c8a-a3de-6f4778c585e5"
    },
    {
        "name": "María García",
        "passport": "X1234567A",
        "client_id": "d78f4683-a2c4-408a-aee6-bc6be6b1df79"
    }
]

print("🧪 Probando nombres de ZIP con nuevo formato:\n")

for test in test_cases:
    sanitized_name = sanitize_name(test["name"])
    sanitized_passport = sanitize_name(test["passport"])
    
    folder_name = f"{sanitized_name}_{sanitized_passport}"
    zip_name = f"{folder_name}.zip"
    
    print(f"Cliente: {test['name']}")
    print(f"Pasaporte/NIE: {test['passport']}")
    print(f"ID: {test['client_id']}")
    print(f"📁 Carpeta dentro del ZIP: {folder_name}/")
    print(f"📦 Nombre del ZIP: {zip_name}")
    print(f"✅ Coinciden: {'SÍ' if zip_name == f'{folder_name}.zip' else 'NO'}")
    print("-" * 70)
