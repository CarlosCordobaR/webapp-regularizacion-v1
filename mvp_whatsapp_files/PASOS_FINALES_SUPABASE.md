# 🎯 Configuración Final de Supabase

## ✅ Completado:
- ✓ API Keys configuradas correctamente
- ✓ Conexión con Supabase verificada
- ✓ Datos mock listos (10 clientes, 118 conversaciones, 21 PDFs)

---

## 📋 Pasos Pendientes (HAZLOS EN ORDEN):

### PASO 1: Ejecutar el Esquema SQL (2 minutos)

**¿Qué hace?** Crea las tablas necesarias en tu base de datos Postgres.

**Instrucciones:**

1. **Abre el SQL Editor:**
   ```
   https://supabase.com/dashboard/project/vqcjovttaucekugwmefj/sql/new
   ```

2. **Copia TODO el contenido** del archivo:
   ```
   mvp_whatsapp_files/backend/app/db/schema.sql
   ```

3. **Pégalo en el editor SQL** (reemplaza cualquier texto que haya)

4. **Presiona el botón "RUN"** (esquina inferior derecha)

5. **Verifica que salga:** `Success. No rows returned`

---

### PASO 2: Crear el Bucket de Storage (1 minuto)

**¿Qué hace?** Crea el almacenamiento para los documentos PDF.

**Instrucciones:**

1. **Ve a Storage:**
   ```
   https://supabase.com/dashboard/project/vqcjovttaucekugwmefj/storage/buckets
   ```

2. **Presiona "New bucket"**

3. **Configura así:**
   - Name: `client-documents`
   - Public bucket: ✓ (marca la casilla)  ← Para MVP, acceso público
   - File size limit: `10 MB` (opcional)
   - Allowed MIME types: `application/pdf` (opcional)

4. **Presiona "Create bucket"**

---

## 🚀 Después de Completar los 2 Pasos:

Ejecuta este comando para sincronizar todos los datos mock a Supabase:

```bash
cd /Users/PhD/Desktop/WebApp_Regularizacion_1/mvp_whatsapp_files/backend

SUPABASE_URL="https://vqcjovttaucekugwmefj.supabase.co" \
SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZxY2pvdnR0YXVjZWt1Z3dtZWZqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDg0MDM5MiwiZXhwIjoyMDg2NDE2MzkyfQ.zp82_hLcg1Ca-Ci2f2Mfe6dgA7s9U2Ugr96t2PM-Kfg" \
STORAGE_BUCKET="client-documents" \
python3 -m app.scripts.sync_mock_to_supabase
```

---

## 📊 Resultados Esperados:

Si todo sale bien, verás:

```
==================================================
SYNC COMPLETE
==================================================
Clients: 10 inserted, 0 updated, 0 skipped
Conversations: 118 inserted, 0 skipped  
Documents: 21 inserted, 0 skipped
Files: 21 uploaded, 0 skipped

Full report: backend/reports/sync_report_TIMESTAMP.json
==================================================
```

---

## ❓ Problemas Comunes:

### "relation clients does not exist"
→ No ejecutaste el PASO 1 (schema.sql)
→ Solución: Ejecuta el esquema SQL completo

### "Storage bucket does not exist"
→ No ejecutaste el PASO 2 (crear bucket)
→ Solución: Crea el bucket en Storage

### "permission denied for table clients"
→ La SERVICE_ROLE_KEY no tiene permisos
→ Solución: Verifica que copiaste la key correcta (empieza con eyJ...)

---

## 🔒 Seguridad:

✅ Las credenciales están guardadas en `.env` (en `.gitignore`)
✅ NUNCA se subirán a GitHub
✅ La `service_role` key es poderosa: mantenla privada

---

## 📝 Siguiente Paso después de Sincronizar:

Una vez sincronizados los datos, podrás cambiar al modo "real" editando `.env`:

```env
APP_MODE=real
STORAGE_MODE=supabase  
DB_MODE=supabase
```

Y tu aplicación usará Supabase en lugar de los datos mock locales.

---

**¿Listo? Completa los PASO 1 y PASO 2, luego avísame para ejecutar la sincronización.**
