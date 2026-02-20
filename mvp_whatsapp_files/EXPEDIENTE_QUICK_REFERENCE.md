# Expediente Feature - Quick Reference

## API Endpoints

### Create Client with Documents
```bash
POST /clients
Content-Type: multipart/form-data

Required Fields:
- full_name: string
- phone_number: string
- passport_or_nie: string  # NEW REQUIRED

Optional Fields:
- profile_type: ASYLUM | ARRAIGO | STUDENT | IRREGULAR | OTHER
- status: active | inactive | archived
- notes: string
- documents: File[]  # PDF files
- document_types: string  # JSON array: ["TASA", "PASSPORT_NIE", null, ...]

Example:
curl -X POST http://localhost:8000/clients \
  -F "full_name=Juan Pérez" \
  -F "phone_number=+34600111222" \
  -F "passport_or_nie=X1234567A" \
  -F "documents=@tasa.pdf" \
  -F "documents=@passport.pdf" \
  -F 'document_types=["TASA", "PASSPORT_NIE"]'
```

### Generate Expediente
```bash
POST /clients/{client_id}/expediente

Response:
- Success (200): application/zip
- Missing client (404): error
- Missing docs (400): {"error": ..., "missing": [...], "message": ...}

Example:
curl -X POST http://localhost:8000/clients/abc-def-123/expediente \
  --output expediente.zip
```

---

## Database Schema

```sql
-- Enum for document types
CREATE TYPE document_type AS ENUM ('TASA', 'PASSPORT_NIE');

-- Clients table
ALTER TABLE clients
ADD COLUMN passport_or_nie TEXT NOT NULL;

-- Documents table
ALTER TABLE documents
ADD COLUMN document_type document_type,
ADD CONSTRAINT unique_client_document_type 
  UNIQUE (client_id, document_type);
```

---

## Frontend Components

### CreateClientModal
```tsx
// New field
<input 
  type="text" 
  id="passport_or_nie"
  value={formData.passport_or_nie}
  required
/>

// Document type selection
<select value={fileWithType.documentType}>
  <option value="">Sin clasificar</option>
  <option value="TASA">Tasa</option>
  <option value="PASSPORT_NIE">Pasaporte/NIE</option>
</select>
```

### ClientTable
```tsx
// Expediente button
<button onClick={(e) => handleGenerateExpediente(e, client.id)}>
  📦 Expediente
</button>

// Download handler
const handleGenerateExpediente = async (e, clientId) => {
  const { blob, filename } = await api.generateExpediente(clientId)
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  window.URL.revokeObjectURL(url)
}
```

---

## Backend Service

### Expediente Service Functions

```python
from app.services.expediente import (
    sanitize_name,
    detect_nie,
    get_document_label,
    generate_expediente_zip,
    MissingDocumentsError
)

# Sanitize client name for filenames
sanitized = sanitize_name("Juan Pérez")  # → "juan_prez"

# Detect if it's a NIE
is_nie = detect_nie("X1234567A")  # → True
is_nie = detect_nie("AB123456")   # → False

# Get label for document
label = get_document_label("X1234567A")  # → "NIE"
label = get_document_label("AB123456")   # → "Pasaporte"

# Generate ZIP
try:
    zip_bytes, folder_name = generate_expediente_zip(client_id)
except MissingDocumentsError as e:
    print(f"Missing: {e.missing}")  # ['TASA'] or ['PASSPORT_NIE']
```

---

## Validation Rules

### passport_or_nie
- **Required**: Cannot be empty
- **Format**: Any string (validated by backend)
- **NIE Detection**: Regex `^[XYZxyz]\d{7}[A-Za-z]$`

### Document Types
- **TASA**: Tax document (required for expediente)
- **PASSPORT_NIE**: Identity document (required for expediente)
- **null**: Unclassified (optional documents)

### Constraints
- One document per type per client (enforced by DB)
- Uploading new document of same type replaces old one
- Only PDF files accepted (10MB max)

---

## ZIP Structure

```
{sanitized_name}_{uuid_short}/
├── Tasa_{sanitized_name}.pdf
└── {NIE|Pasaporte}_{sanitized_name}.pdf
```

### Example
Client: "María José López", ID: `a3b4c5d6-1234-...`, NIE: `X7654321B`

```
maria_jos_lpez_a3b4c5d6/
├── Tasa_maria_jos_lpez.pdf
└── NIE_maria_jos_lpez.pdf
```

---

## Error Handling

### Frontend
```typescript
try {
  const { blob, filename } = await api.generateExpediente(clientId)
  // Download...
} catch (err) {
  // Show error to user
  alert(err.message)
  // Example: "Missing documents: TASA, PASSPORT_NIE..."
}
```

### Backend
```python
from app.services.expediente import MissingDocumentsError

try:
    zip_bytes, folder_name = generate_expediente_zip(client_id)
except ValueError:
    # Client not found
    raise HTTPException(status_code=404, detail="Client not found")
except MissingDocumentsError as e:
    # Missing required documents
    raise HTTPException(
        status_code=400,
        detail={
            "error": "Missing required documents",
            "missing": e.missing,
            "message": "Cannot generate expediente..."
        }
    )
```

---

## Testing Quick Commands

### Create Test Client
```bash
curl -X POST http://localhost:8000/clients \
  -F "full_name=Test User" \
  -F "phone_number=+34600000000" \
  -F "passport_or_nie=X0000000A" \
  -F "profile_type=OTHER"
```

### Upload TASA Document
```bash
curl -X POST http://localhost:8000/clients/{id}/documents \
  -F "documents=@tasa.pdf" \
  -F 'document_types=["TASA"]'
```

### Upload PASSPORT_NIE Document
```bash
curl -X POST http://localhost:8000/clients/{id}/documents \
  -F "documents=@passport.pdf" \
  -F 'document_types=["PASSPORT_NIE"]'
```

### Generate Expediente
```bash
curl -X POST http://localhost:8000/clients/{id}/expediente \
  --output test_expediente.zip
```

### Verify ZIP Contents
```bash
unzip -l test_expediente.zip
# Should show:
# test_user_a3b4c5d6/Tasa_test_user.pdf
# test_user_a3b4c5d6/NIE_test_user.pdf
```

---

## Migration Commands

### Development (Local)
```bash
# Apply migrations
psql whatsapp_db < backend/app/db/migrations/001_add_passport_or_nie.sql
psql whatsapp_db < backend/app/db/migrations/002_add_document_type.sql
```

### Production (Supabase)
```bash
# Connect to Supabase
psql "postgresql://postgres:[password]@[host]:5432/postgres"

# Run migrations
\i backend/app/db/migrations/001_add_passport_or_nie.sql
\i backend/app/db/migrations/002_add_document_type.sql
```

---

## Common SQL Queries

### Check Client Documents
```sql
SELECT 
  d.id,
  d.original_filename,
  d.document_type,
  d.uploaded_at
FROM documents d
WHERE d.client_id = 'abc-def-123'
ORDER BY d.uploaded_at DESC;
```

### Find Clients Missing passport_or_nie
```sql
SELECT id, name, phone_number
FROM clients
WHERE passport_or_nie IS NULL 
   OR passport_or_nie = 'PENDING';
```

### Find Clients Missing Required Docs
```sql
SELECT 
  c.id,
  c.name,
  CASE WHEN tasa.id IS NULL THEN 'MISSING' ELSE 'OK' END as tasa_status,
  CASE WHEN nie.id IS NULL THEN 'MISSING' ELSE 'OK' END as nie_status
FROM clients c
LEFT JOIN documents tasa ON c.id = tasa.client_id AND tasa.document_type = 'TASA'
LEFT JOIN documents nie ON c.id = nie.client_id AND nie.document_type = 'PASSPORT_NIE'
WHERE tasa.id IS NULL OR nie.id IS NULL;
```

### Count Documents by Type
```sql
SELECT 
  document_type,
  COUNT(*) as count
FROM documents
GROUP BY document_type;
```

---

## Environment Variables

### Backend (.env)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key  # Required for storage access
SUPABASE_ANON_KEY=your-anon-key
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

---

## File Locations

### Backend
```
backend/
├── app/
│   ├── api/
│   │   └── clients.py              # Updated endpoints
│   ├── models/
│   │   ├── enums.py                # DocumentType enum
│   │   └── dto.py                  # Updated DTOs
│   ├── services/
│   │   └── expediente.py           # NEW: ZIP generation
│   └── db/
│       └── migrations/
│           ├── 001_add_passport_or_nie.sql
│           └── 002_add_document_type.sql
```

### Frontend
```
frontend/
├── src/
│   ├── components/
│   │   ├── CreateClientModal.tsx   # Updated with passport_or_nie
│   │   └── ClientTable.tsx         # Added expediente button
│   ├── lib/
│   │   └── api.ts                  # New generateExpediente method
│   └── pages/
│       └── Clients.tsx
```

---

## Performance Notes

- **ZIP Generation**: In-memory (fast for small files)
- **File Download**: Supabase Storage direct download
- **Database Query**: 2 queries (client + documents)
- **Network**: Single ZIP download (efficient)

### Optimization Tips
1. Use pagination for large document lists
2. Cache client documents in frontend
3. Implement retry logic for failed downloads
4. Add progress indicator for large ZIPs

---

## Security Considerations

1. **Service Role Key**: Keep secret, use for storage access only
2. **File Validation**: Backend validates PDF type and size
3. **Unique Constraint**: Prevents duplicate document types
4. **Input Sanitization**: Names sanitized before use in filenames
5. **Access Control**: Expediente can only be generated by authenticated users

---

## Support

For issues or questions:
1. Check [EXPEDIENTE_FEATURE_GUIDE.md](./EXPEDIENTE_FEATURE_GUIDE.md) for detailed docs
2. Review migration files for database setup
3. Check error messages in browser console (frontend) or logs (backend)
4. Verify Supabase Storage permissions
5. Ensure SERVICE_ROLE_KEY has storage access
