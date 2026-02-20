#!/usr/bin/env python3
"""Test Prisma with real models from introspection"""
import asyncio
from prisma import Prisma
from prisma.models import Client, Document, Conversation

async def test_prisma_queries():
    db = Prisma()
    try:
        await db.connect()
        print('✅ Prisma conectado exitosamente!\n')
        
        # Test 1: Count all clients
        client_count = await db.client.count()
        print(f'📊 Total clientes: {client_count}')
        
        # Test 2: Get first client with documents
        client = await db.client.find_first(
            include={'documents': True, 'conversations': True}
        )
        if client:
            print(f'👤 Cliente: {client.name} ({client.phoneNumber})')
            print(f'   - Documentos: {len(client.documents)}')
            print(f'   - Conversaciones: {len(client.conversations)}')
        
        # Test 3: Count documents by type
        tasa_count = await db.document.count(where={'documentType': 'TASA'})
        nie_count = await db.document.count(where={'documentType': 'PASSPORT_NIE'})
        print(f'\n📄 Documentos:')
        print(f'   - TASA: {tasa_count}')
        print(f'   - PASSPORT/NIE: {nie_count}')
        
        # Test 4: Recent conversations
        recent = await db.conversation.find_many(
            order={'createdAt': 'desc'},
            take=3
        )
        print(f'\n💬 Últimas {len(recent)} conversaciones:')
        for conv in recent:
            print(f'   - {conv.messageType}: {conv.content[:50]}...')
        
        print('\n🎉 ¡Todas las queries funcionan correctamente!')
        print('✅ Prisma está completamente configurado y listo para usar')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        await db.disconnect()

if __name__ == '__main__':
    asyncio.run(test_prisma_queries())
