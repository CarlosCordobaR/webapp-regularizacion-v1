#!/bin/bash
# Script de Configuración de Supabase
# ====================================
# Este script te ayuda a configurar y verificar tu conexión con Supabase

echo "🔧 Asistente de Configuración de Supabase"
echo "=========================================="
echo ""
echo "⚠️  INFORMACIÓN REQUERIDA:"
echo ""
echo "Para completar la integración con Supabase, necesitas obtener las"
echo "siguientes credenciales desde tu Dashboard de Supabase:"
echo ""
echo "1. 📍 SUPABASE_URL"
echo "   - Ve a: https://supabase.com/dashboard/project/_/settings/api"
echo "   - Busca: 'Project URL'"
echo "   - Formato: https://xxxproject.supabase.co"
echo ""
echo "2. 🔑 SUPABASE_SERVICE_ROLE_KEY"
echo "   - En la misma página de API settings"
echo "   - Busca: 'service_role secret'"
echo "   - ⚠️  Es un JWT largo que empieza con 'eyJ...'"
echo "   - ⚠️  NUNCA compartas esta key públicamente"
echo ""
echo "3. 🔐 SUPABASE_ANON_KEY (opcional para frontend)"
echo "   - En la misma página"
echo "   - Busca: 'anon public'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 ESTADO ACTUAL:"
echo ""

# Verificar variables de entorno
if [ -f .env ]; then
    echo "✅ Archivo .env encontrado"
    
    SUPABASE_URL=$(grep "^SUPABASE_URL=" .env | cut -d '=' -f2)
    SUPABASE_KEY=$(grep "^SUPABASE_SERVICE_ROLE_KEY=" .env | cut -d '=' -f2)
    
    if [[ $SUPABASE_URL == *"your-project-id"* ]]; then
        echo "❌ SUPABASE_URL no configurada (placeholder detectado)"
    else
        echo "✅ SUPABASE_URL: $SUPABASE_URL"
    fi
    
    if [[ $SUPABASE_KEY == "your-service-key" ]] || [[ $SUPABASE_KEY == *"sb_secret__"* ]]; then
        echo "❌ SUPABASE_SERVICE_ROLE_KEY no válida"
        echo "   Formato incorrecto. Debe ser un JWT que empiece con 'eyJ...'"
    elif [[ $SUPABASE_KEY == eyJ* ]]; then
        echo "✅ SUPABASE_SERVICE_ROLE_KEY configurada (JWT válido)"
    else
        echo "⚠️  SUPABASE_SERVICE_ROLE_KEY: Formato desconocido"
    fi
else
    echo "❌ Archivo .env no encontrado"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 SIGUIENTE PASOS:"
echo ""
echo "1. Abre tu Dashboard de Supabase"
echo "2. Copia las credenciales correctas"
echo "3. Edita el archivo .env con las credenciales reales"
echo "4. Ejecuta: python3 -m app.scripts.create_supabase_users"
echo "5. Ejecuta: python3 -m app.scripts.sync_mock_to_supabase"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 AYUDA:"
echo ""
echo "Si no tienes un proyecto Supabase:"
echo "  1. Ve a https://supabase.com"
echo "  2. Crea una cuenta gratuita"
echo "  3. Crea un nuevo proyecto"
echo "  4. Espera ~2 minutos a que se aprovisione"
echo "  5. Ve a Settings → API para obtener las credenciales"
echo ""
echo "Documentación: https://supabase.com/docs/guides/api"
echo ""
