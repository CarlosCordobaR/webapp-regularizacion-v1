# 🔷 Prisma Database Management Guide

## 📋 Quick Reference

Prisma es tu interface principal para modificaciones de base de datos. **TODO desde VS Code, sin tocar Supabase Dashboard**.

---

## 🚀 Inicial Setup (Solo una vez)

### ✅ SETUP COMPLETADO

Tu base de datos Prisma ya está configurada y funcionando:

- ✅ DATABASE_URL configurado (connection pooling)
- ✅ DIRECT_URL configurado (para migraciones)
- ✅ Cliente Prisma generado (v0.15.0)
- ✅ Schema sincronizado con Supabase
- ✅ Queries probadas y funcionando

**Conectado a**: Supabase PostgreSQL (16 clientes, 29 documentos, 118 conversaciones)

---

## 📝 Workflow Diario

### Modificar Schema (Agregar Columna/Tabla)

**1. Editar `backend/prisma/schema.prisma`**:

```prisma
model Client {
  // ...campos existentes...
  email String? @db.VarChar(255)  // ← NUEVA COLUMNA
}
```

**2. Crear y aplicar migration**:

```bash
# Genera SQL automáticamente y aplica a DB
python3 app/scripts/prisma_setup.py migrate add_email_to_clients
```

**3. Re-generar cliente**:

```bash
python3 -m prisma generate
```

**¡Listo!** La columna existe en Supabase y tu código Python tiene tipos actualizados.

---

## 🛠️ Comandos Principales

### Setup y Generación

**Opción 1: Usando el script helper (RECOMENDADO)**

```bash
# Generar cliente Prisma (después de cambios en schema)
./prisma.sh generate

# Ver schema actual de DB (introspección)
./prisma.sh db pull

# Validar sintaxis de schema.prisma
./prisma.sh validate

# Formatear schema.prisma
./prisma.sh format

# Abrir Prisma Studio (navegador de DB visual)
./prisma.sh studio
```

**Opción 2: Comando completo (si el script no funciona)**

```bash
export PATH="/Users/PhD/Library/Python/3.9/bin:$PATH"
python3 -m prisma generate
python3 -m prisma db pull
python3 -m prisma validate
python3 -m prisma format
```

### Migrations

```bash
# Crear nueva migration
./prisma.sh migrate dev --name <nombre>

# Ejemplos:
./prisma.sh migrate dev --name add_email_field
./prisma.sh migrate dev --name create_payments_table

# Ver migrations pendientes
ls prisma/migrations/

# Aplicar migrations (producción)
./prisma.sh migrate deploy

# Reset DB completo (DESTRUCTIVO - solo dev)
./prisma.sh migrate reset

# Ver estado de migrations
./prisma.sh migrate status
```

### Ayuda

```bash
# Ver todos los comandos disponibles
python3 app/scripts/prisma_setup.py help
```

---

## 📚 Ejemplos Comunes

### Ejemplo 1: Agregar Columna

```prisma
// prisma/schema.prisma
model Client {
  // ...existing...
  email      String?   @db.VarChar(255)
  birthDate  DateTime? @map("birth_date")
}
```

```bash
python3 app/scripts/prisma_setup.py migrate add_client_fields
python3 -m prisma generate
```

### Ejemplo 2: Crear Nueva Tabla

```prisma
// prisma/schema.prisma
model Payment {
  id        String   @id @default(dbgenerated("uuid_generate_v4()")) @db.Uuid
  clientId  String   @map("client_id") @db.Uuid
  amount    Decimal  @db.Decimal(10, 2)
  paidAt    DateTime @default(now()) @map("paid_at")
  
  client    Client   @relation(fields: [clientId], references: [id])
  
  @@map("payments")
}

// Agregar relación en Client
model Client {
  // ...
  payments  Payment[]
}
```

```bash
python3 app/scripts/prisma_setup.py migrate create_payments_table
python3 -m prisma generate
```

### Ejemplo 3: Modificar Enum

```prisma
enum DocumentType {
  TASA
  PASSPORT_NIE
  VISA           // ← NUEVO
  WORK_PERMIT    // ← NUEVO
}
```

```bash
python3 app/scripts/prisma_setup.py migrate add_document_types
python3 -m prisma generate
```

---

## 💻 Usar Prisma en Código

### Importar Cliente

```python
from app.db.prisma_client import get_prisma

async def my_function():
    db = await get_prisma()
    
    # Tu código aquí
    clients = await db.client.find_many()
```

### CRUD Básico

```python
# CREATE
client = await db.client.create({
    'phoneNumber': '+34600111222',
    'name': 'Juan Pérez',
    'passportOrNie': 'X1234567A',
    'profileType': 'ASYLUM'
})

# READ
client = await db.client.find_unique(
    where={'phoneNumber': '+34600111222'}
)

clients = await db.client.find_many(
    where={'status': 'active'},
    include={'documents': True},
    order={'createdAt': 'desc'}
)

# UPDATE
updated = await db.client.update(
    where={'id': client_id},
    data={'name': 'Juan Updated'}
)

# DELETE
await db.client.delete(where={'id': client_id})
```

### Queries Avanzados

```python
# Paginación
clients = await db.client.find_many(
    skip=(page - 1) * page_size,
    take=page_size
)

# Búsqueda con OR
results = await db.client.find_many(
    where={
        'OR': [
            {'name': {'contains': 'Juan'}},
            {'phoneNumber': {'contains': '600'}}
        ]
    }
)

# Contar
count = await db.document.count(
    where={'documentType': 'TASA'}
)
```

Ver más ejemplos en: `backend/app/db/prisma_client.py`

---

## 🔄 Integración con FastAPI

### Startup/Shutdown

```python
# app/main.py
from app.db.prisma_client import connect_prisma, disconnect_prisma

@app.on_event("startup")
async def startup():
    await connect_prisma()

@app.on_event("shutdown")
async def shutdown():
    await disconnect_prisma()
```

### Endpoint Example

```python
# app/api/clients.py
from app.db.prisma_client import get_prisma

@router.get("/clients")
async def list_clients():
    db = await get_prisma()
    clients = await db.client.find_many(
        include={'documents': True}
    )
    return clients
```

---

## 📖 Recursos

- **Prisma Docs**: https://prisma-client-py.readthedocs.io/
- **Schema Reference**: https://www.prisma.io/docs/reference/api-reference/prisma-schema-reference
- **VS Code Extension**: [Prisma](https://marketplace.visualstudio.com/items?itemName=Prisma.prisma)

---

## 🚨 Troubleshooting

### Error: "Environment variable not found: DATABASE_URL"

**Solución**: Verifica que `backend/.env` existe y contiene `DATABASE_URL`.

### Error: "Prisma Client not generated"

**Solución**:
```bash
python3 -m prisma generate
```

### Error: "Migration failed"

**Solución**: Revisa el error, posiblemente conflicto con datos existentes. Puedes:
1. Modificar migration en `prisma/migrations/`
2. O revertir con `prisma migrate resolve --rolled-back <migration_name>`

### Schema out of sync

**Solución**:
```bash
# Ver estado actual
python3 -m prisma migrate status

# Forzar sincronización (cuidado en producción)
python3 -m prisma migrate reset
```

---

## ✅ Checklist de Desarrollo

Cuando modificas la base de datos:

- [ ] ✏️ Editar `prisma/schema.prisma`
- [ ] 🔄 Crear migration: `python3 app/scripts/prisma_setup.py migrate <nombre>`
- [ ] ⚙️ Generar cliente: `python3 -m prisma generate`
- [ ] 🧪 Probar en código Python
- [ ] 📝 Commit migration files a Git
- [ ] 🚀 Deployar: `python3 app/scripts/prisma_setup.py deploy` (producción)

---

## 🎯 Ventajas vs SQL Manual

| Feature | SQL Manual | **Prisma** |
|---------|-----------|------------|
| Type Safety | ❌ | ✅ |
| Autocompletado | ❌ | ✅ |
| Migrations versionadas | ⚠️ Manual | ✅ Auto |
| Rollback | ❌ | ✅ |
| Team collaboration | ⚠️ Difícil | ✅ Git-friendly |
| Preview changes | ❌ | ✅ |

**Resultado**: Menos errores, más velocidad, mejor colaboración.
