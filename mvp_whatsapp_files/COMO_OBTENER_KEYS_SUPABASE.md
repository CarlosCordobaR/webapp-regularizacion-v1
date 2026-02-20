# 🔑 Cómo Obtener las API Keys Correctas de Supabase

## ⚠️ IMPORTANTE: Las keys que me diste NO son válidas

Las keys `sb_publishable_...` y `sb_secret_...` **NO SON** las API keys de Supabase.

---

## 📍 Pasos para obtener las keys correctas:

### PASO 1: Ve a tu Dashboard de Supabase

Abre esta URL exacta en tu navegador:
```
https://supabase.com/dashboard/project/vqcjovttaucekugwmefj/settings/api
```

### PASO 2: Busca la sección "Project API keys"

En esa página, desplázate hacia abajo hasta que veas una sección llamada **"Project API keys"**.

Deberías ver algo similar a esto:

```
┌──────────────────────────────────────────────────────────┐
│  Project API keys                                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  📌 Project URL                                          │
│  https://vqcjovttaucekugwmefj.supabase.co              │
│                                                          │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  🔑 anon public                                          │
│  This key is safe to use in a browser                   │
│  [••••••••••••••••••••••••••] [👁 Show] [📋 Copy]       │
│                                                          │
│  ─────────────────────────────────────────────────────  │
│                                                          │
│  🔐 service_role secret                                  │
│  This key has the ability to bypass Row Level Security  │
│  [••••••••••••••••••••••••••] [👁 Show] [📋 Copy]       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### PASO 3: Presiona el botón "Show" o "Copy"

Para cada una de estas keys:

#### A) `anon public` key:
1. Presiona el botón **[👁 Show]** o **[📋 Copy]**
2. Verás un token MUY LARGO que empieza así:
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZxY2pvdnR0YXVjZWt1Z3dtZWZqIiwicm9sZSI6ImFub24iLCJpYXQiOjE2...
   ```
3. **Este token tiene aproximadamente 200-300 caracteres de largo**
4. **Tiene 3 partes separadas por puntos (.)**

#### B) `service_role secret` key:
1. Presiona el botón **[👁 Show]** o **[📋 Copy]**
2. Verás otro token MUY LARGO que también empieza así:
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZxY2pvdnR0YXVjZWt1Z3dtZWZqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTY...
   ```
3. **Este token TAMBIÉN tiene aproximadamente 200-300 caracteres de largo**
4. **También tiene 3 partes separadas por puntos (.)**

---

## ✅ Características de las keys CORRECTAS:

- ✓ Empiezan con: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.`
- ✓ Son MUY largas (200-300+ caracteres)
- ✓ Tienen 3 partes separadas por puntos (.)
- ✓ Parecen texto aleatorio después del primer punto
- ✓ Son tokens JWT (JSON Web Token)

## ❌ LO QUE NO SON:

- ✗ `sb_publishable_...` ← NO es la key correcta
- ✗ `sb_secret_...` ← NO es la key correcta
- ✗ Keys cortas (menos de 100 caracteres)
- ✗ JSON objects con `x`, `y`, `alg`, etc.

---

## 🎯 Lo que necesito que hagas:

1. Ve a: https://supabase.com/dashboard/project/vqcjovttaucekugwmefj/settings/api
2. Busca "Project API keys"
3. Presiona [Show] en **anon public**
4. Copia TODO el token largo (empieza con eyJ...)
5. Presiona [Show] en **service_role secret**
6. Copia TODO el token largo (empieza con eyJ...)
7. Pégame ambos tokens aquí

---

## 💡 EJEMPLO de cómo se ven (ESTO ES UN EJEMPLO, NO LO USES):

```
anon public:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4YW1wbGUiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxMTc3MDQwMCwiZXhwIjoxOTI3MzQ2NDAwfQ.dummysignaturehere123456789

service_role secret:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4YW1wbGUiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjExNzcwNDAwLCJleHAiOjE5MjczNDY0MDB9.anotherdummysignature123456789
```

**TUS keys se verán similares pero con valores diferentes.**

---

## 🔒 Nota de Seguridad:

Una vez que me des la `service_role secret` key, la guardaré SOLO en tu archivo `.env` local que está en `.gitignore` y NUNCA se subirá a GitHub. Esta key es muy poderosa y no debe compartirse públicamente.

---

**¿Puedes ir a esa página y copiar ambas keys completas?**
