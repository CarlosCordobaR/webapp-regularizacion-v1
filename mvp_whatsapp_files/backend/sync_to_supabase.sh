#!/bin/bash
# Script para Sincronizar Datos Mock a Supabase
# =============================================

echo "🔐 Cargando credenciales desde .env..."

# Navegar al directorio backend
cd "$(dirname "$0")"

# Exportar variables desde .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "❌ Error: Archivo .env no encontrado"
    exit 1
fi

echo "✅ Credenciales cargadas"
echo "📍 URL: $SUPABASE_URL"
echo "📦 Bucket: $STORAGE_BUCKET"
echo ""

# Verificar que las variables estén configuradas
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "❌ Error: Variables SUPABASE no están configuradas en .env"
    exit 1
fi

echo "🚀 Iniciando sincronización de datos mock a Supabase..."
echo "════════════════════════════════════════════════════════"
echo ""

# Ejecutar script de sincronización
python3 -m app.scripts.sync_mock_to_supabase

SYNC_EXIT_CODE=$?

echo ""
echo "════════════════════════════════════════════════════════"

if [ $SYNC_EXIT_CODE -eq 0 ]; then
    echo "✅ ¡Sincronización completada exitosamente!"
    echo ""
    echo "📊 Puedes ver el reporte detallado en:"
    echo "   backend/reports/sync_report_*.json"
    echo ""
    echo "🎯 Siguiente paso:"
    echo "   Cambia APP_MODE=real en .env para usar Supabase"
else
    echo "❌ Error durante la sincronización"
    echo ""
    echo "💡 Problemas comunes:"
    echo "   1. ¿Ejecutaste el schema.sql en Supabase SQL Editor?"
    echo "   2. ¿Creaste el bucket 'client-documents' en Storage?"
    echo "   3. ¿Las credenciales en .env son correctas?"
    echo ""
    echo "📖 Ver: PASOS_FINALES_SUPABASE.md para más ayuda"
fi

exit $SYNC_EXIT_CODE
