#!/usr/bin/env python3
"""
Script de migración para mover datos de metadata.notes al campo notes directo.

Este script:
1. Conecta a la base de datos usando Supabase
2. Lee todos los clientes que tienen metadata.notes
3. Migra el valor al campo notes
4. Opcionalmente limpia metadata.notes
5. Genera un reporte de la migración

Uso:
    python3 migrate_notes_field.py [--dry-run] [--clean-metadata]
    
Opciones:
    --dry-run: Solo muestra qué se haría sin realizar cambios
    --clean-metadata: Elimina metadata.notes después de migrar
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.supabase import SupabaseClient

setup_logging()
logger = get_logger(__name__)


async def migrate_notes(dry_run: bool = False, clean_metadata: bool = False) -> Dict:
    """
    Migra notas de metadata.notes al campo notes.
    
    Args:
        dry_run: Si es True, solo simula la migración
        clean_metadata: Si es True, elimina metadata.notes después de migrar
        
    Returns:
        Dict con estadísticas de la migración
    """
    logger.info("=" * 60)
    logger.info("INICIANDO MIGRACIÓN DE NOTAS")
    logger.info("=" * 60)
    logger.info(f"Modo: {'DRY RUN (simulación)' if dry_run else 'PRODUCCIÓN'}")
    logger.info(f"Limpiar metadata: {clean_metadata}")
    logger.info("")
    
    # Conectar a Supabase
    supabase = SupabaseClient()
    
    stats = {
        "total_clients": 0,
        "clients_with_metadata_notes": 0,
        "clients_already_migrated": 0,
        "clients_to_migrate": 0,
        "successfully_migrated": 0,
        "errors": 0,
        "error_details": [],
    }
    
    try:
        # 1. Obtener todos los clientes
        logger.info("📊 Obteniendo todos los clientes...")
        response = supabase.client.table("clients").select("*").execute()
        all_clients = response.data
        stats["total_clients"] = len(all_clients)
        logger.info(f"   Total de clientes: {stats['total_clients']}")
        
        # 2. Filtrar clientes que necesitan migración
        clients_to_migrate = []
        
        for client in all_clients:
            client_id = client['id']
            metadata = client.get('metadata', {})
            current_notes = client.get('notes', '')
            metadata_notes = metadata.get('notes', '') if isinstance(metadata, dict) else ''
            
            # Contar clientes con metadata.notes
            if metadata_notes:
                stats["clients_with_metadata_notes"] += 1
                
                # Si notes ya tiene valor y es igual a metadata.notes, se considera migrado
                if current_notes == metadata_notes:
                    stats["clients_already_migrated"] += 1
                    logger.debug(f"   ✓ Cliente {client_id[:8]}... ya migrado")
                else:
                    # Necesita migración
                    clients_to_migrate.append({
                        'id': client_id,
                        'name': client.get('name', 'Sin nombre'),
                        'metadata_notes': metadata_notes,
                        'current_notes': current_notes,
                        'metadata': metadata,
                    })
                    stats["clients_to_migrate"] += 1
        
        logger.info(f"\n📋 ANÁLISIS:")
        logger.info(f"   • Clientes con metadata.notes: {stats['clients_with_metadata_notes']}")
        logger.info(f"   • Ya migrados: {stats['clients_already_migrated']}")
        logger.info(f"   • Necesitan migración: {stats['clients_to_migrate']}")
        
        # 3. Realizar migración
        if stats["clients_to_migrate"] > 0:
            logger.info(f"\n🔄 {'SIMULANDO' if dry_run else 'REALIZANDO'} MIGRACIÓN...")
            
            for i, client_data in enumerate(clients_to_migrate, 1):
                client_id = client_data['id']
                name = client_data['name']
                metadata_notes = client_data['metadata_notes']
                current_notes = client_data['current_notes']
                
                logger.info(f"\n   [{i}/{stats['clients_to_migrate']}] Cliente: {name} ({client_id[:8]}...)")
                logger.info(f"       metadata.notes: {metadata_notes[:50]}...")
                logger.info(f"       notes actual: {current_notes[:50] if current_notes else '(vacío)'}...")
                
                if not dry_run:
                    try:
                        # Preparar datos de actualización
                        update_data = {
                            'notes': metadata_notes,
                            'updated_at': datetime.utcnow().isoformat(),
                        }
                        
                        # Si se solicita limpiar metadata
                        if clean_metadata:
                            new_metadata = client_data['metadata'].copy()
                            if 'notes' in new_metadata:
                                del new_metadata['notes']
                            update_data['metadata'] = new_metadata
                        
                        # Ejecutar actualización
                        response = supabase.client.table("clients").update(update_data).eq("id", client_id).execute()
                        
                        if response.data:
                            stats["successfully_migrated"] += 1
                            logger.info(f"       ✓ Migrado exitosamente")
                        else:
                            raise Exception("No se recibió respuesta de la base de datos")
                            
                    except Exception as e:
                        stats["errors"] += 1
                        error_msg = f"Error en cliente {client_id[:8]}: {str(e)}"
                        stats["error_details"].append(error_msg)
                        logger.error(f"       ✗ {error_msg}")
                else:
                    stats["successfully_migrated"] += 1
                    logger.info(f"       ✓ Se migraría (DRY RUN)")
        else:
            logger.info("\n✅ No hay clientes que necesiten migración")
        
        # 4. Reporte final
        logger.info("\n" + "=" * 60)
        logger.info("REPORTE DE MIGRACIÓN")
        logger.info("=" * 60)
        logger.info(f"Total de clientes: {stats['total_clients']}")
        logger.info(f"Clientes con metadata.notes: {stats['clients_with_metadata_notes']}")
        logger.info(f"Ya migrados: {stats['clients_already_migrated']}")
        logger.info(f"Necesitaban migración: {stats['clients_to_migrate']}")
        logger.info(f"{'Simulados' if dry_run else 'Migrados'} exitosamente: {stats['successfully_migrated']}")
        logger.info(f"Errores: {stats['errors']}")
        
        if stats["error_details"]:
            logger.info("\nDETALLE DE ERRORES:")
            for error in stats["error_details"]:
                logger.error(f"  • {error}")
        
        logger.info("=" * 60)
        
        # Guardar reporte en archivo
        report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(stats, f, indent=2)
        logger.info(f"\n📄 Reporte guardado en: {report_file}")
        
        return stats
        
    except Exception as e:
        logger.error(f"\n❌ Error fatal durante la migración: {e}")
        raise


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Migrar notas de metadata.notes al campo notes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular la migración sin realizar cambios',
    )
    parser.add_argument(
        '--clean-metadata',
        action='store_true',
        help='Eliminar metadata.notes después de migrar (solo con producción)',
    )
    
    args = parser.parse_args()
    
    # Verificar configuración
    try:
        settings = get_settings()
        logger.info(f"🔧 Configuración cargada - Entorno: {settings.environment}")
    except Exception as e:
        logger.error(f"❌ Error cargando configuración: {e}")
        sys.exit(1)
    
    # Confirmar si no es dry run
    if not args.dry_run:
        logger.warning("\n⚠️  ATENCIÓN: Vas a modificar la base de datos de PRODUCCIÓN")
        response = input("¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
        if response != 'SI':
            logger.info("❌ Operación cancelada por el usuario")
            sys.exit(0)
    
    # Ejecutar migración
    try:
        stats = asyncio.run(migrate_notes(
            dry_run=args.dry_run,
            clean_metadata=args.clean_metadata
        ))
        
        if stats["errors"] > 0:
            logger.warning(f"\n⚠️  Migración completada con {stats['errors']} errores")
            sys.exit(1)
        else:
            logger.info("\n✅ Migración completada exitosamente")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"\n❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
