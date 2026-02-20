#!/usr/bin/env python3
"""Test Prisma database connection"""
import asyncio
from prisma import Prisma

async def test_connection():
    db = Prisma()
    try:
        await db.connect()
        print('✅ Conexión a Supabase exitosa!')
        
        # Contar clientes
        result = await db.query_raw('SELECT COUNT(*) as count FROM clients')
        print(f'📊 Clientes en DB: {result[0]["count"]}')
        
        # Contar documentos
        result = await db.query_raw('SELECT COUNT(*) as count FROM documents')
        print(f'📄 Documentos en DB: {result[0]["count"]}')
        
        # Contar conversaciones
        result = await db.query_raw('SELECT COUNT(*) as count FROM conversations')
        print(f'💬 Conversaciones en DB: {result[0]["count"]}')
        
        print('\n🎉 ¡Prisma está listo para usar!')
        
    except Exception as e:
        print(f'❌ Error de conexión: {e}')
    finally:
        await db.disconnect()

if __name__ == '__main__':
    asyncio.run(test_connection())
