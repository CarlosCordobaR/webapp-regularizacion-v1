# Expediente Generation Feature - Implementation Summary

## Overview

The "Generar Expediente" feature allows users to generate a ZIP file containing all required documents for a client in a standardized format. This feature enforces document classification and ensures that all necessary documentation is present before generating the expediente package.

---

## Feature Requirements

### Required Fields
- **passport_or_nie**: Every client must have a Passport number or NIE (Spanish ID for foreigners)
- **TASA document**: Required tax document
- **PASSPORT_NIE document**: Required identity document (Passport or NIE)

### ZIP File Structure
```
{Client_Name}_{Client_ID_Short}/
├── Tasa_{sanitized_name}.pdf
└── {NIE|Pasaporte}_{sanitized_name}.pdf
```

**Example**: `juan_perez_#a3b4c5d6/Tasa_juan_perez.pdf`

### Naming Rules
1. **Folder name**: `{sanitized_name}_{first_8_chars_of_uuid}`
   - Client name sanitized: lowercase, spaces → underscores, special chars removed
   - First 8 characters of client UUID (e.g., `#a3b4c5d6`)

2. **TASA document**: Always named `Tasa_{sanitized_name}.pdf`

3. **Identity document**: Named based on NIE detection:
   - If NIE format detected (`^[XYZxyz]\d{7}[A-Za-z]$`): `NIE_{sanitized_name}.pdf`
   - Otherwise: `Pasaporte_{sanitized_name}.pdf`

---

## Database Changes

### Schema Updates

#### 1. New Enum Type
```sql
CREATE TYPE document_type AS ENUM ('TASA', 'PASSPORT_NIE');
```

#### 2. Clients Table Addition
```sql
ALTER TABLE clients
ADD COLUMN passport_or_nie TEXT NOT NULL;
```

#### 3. Documents Table Addition
```sql
ALTER TABLE documents
ADD COLUMN document_type document_type;

ALTER TABLE documents
ADD CONSTRAINT unique_client_document_type UNIQUE (client_id, document_type);
```

**Important**: The unique constraint ensures only ONE document per type per client. Uploading a new document of the same type will replace the old one.

### Migration Files
- `backend/app/db/migrations/001_add_passport_or_nie.sql`
- `backend/app/db/migrations/002_add_document_type.sql`

---

## Backend Implementation

### 1. Models & DTOs

**New Enum** (`app/models/enums.py`):
```python
class DocumentType(str, Enum):
    TASA = "TASA"
    PASSPORT_NIE = "PASSPORT_NIE"
```

**Updated DTOs** (`app/models/dto.py`):
- `ClientCreateRequest`: Added `passport_or_nie: str` (required)
- `DocumentBase`: Added `document_type: Optional[DocumentType]`
- `DocumentCreate`: Added validator for `document_type`

### 2. API Endpoints

#### POST /clients
**Changes**:
- Now requires `passport_or_nie` field
- Accepts optional `document_types` parameter (JSON array)
- Documents can be classified during upload

**Example Request**:
```bash
curl -X POST http://localhost:8000/clients \
  -F "full_name=Juan Pérez" \
  -F "phone_number=+34600111222" \
  -F "passport_or_nie=X1234567A" \
  -F "profile_type=STUDENT" \
  -F "documents=@tasa.pdf" \
  -F "documents=@passport.pdf" \
  -F 'document_types=["TASA", "PASSPORT_NIE"]'
```

#### PUT /clients/{id}
**Changes**:
- Accepts optional `passport_or_nie` update
- Supports `document_types` parameter
- Implements document upsert: replaces existing docs with same type

#### POST /clients/{id}/documents
**Changes**:
- Accepts optional `document_types` parameter
- Implements document upsert logic

#### POST /clients/{id}/expediente ⭐ NEW
**Description**: Generates expediente ZIP file for download

**Response**:
- Success (200): ZIP file with `Content-Disposition` header
- Missing client (404): Client not found error
- Missing docs (400): List of missing required documents

**Error Example**:
```json
{
  "error": "Missing required documents",
  "missing": ["TASA", "PASSPORT_NIE"],
  "message": "Cannot generate expediente. Please upload all required documents (TASA and PASSPORT_NIE)."
}
```

### 3. Expediente Service

**File**: `backend/app/services/expediente.py`

**Key Functions**:
1. `sanitize_name(name: str) -> str`
   - Converts spaces to underscores
   - Removes special characters
   - Returns lowercase string

2. `detect_nie(passport_or_nie: str) -> bool`
   - Regex: `^[XYZxyz]\d{7}[A-Za-z]$`
   - Returns True for Spanish NIE format

3. `get_document_label(passport_or_nie: str) -> str`
   - Returns "NIE" or "Pasaporte" based on detection

4. `generate_expediente_zip(client_id: UUID) -> Tuple[bytes, str]`
   - Main function that orchestrates ZIP creation
   - Downloads PDFs from Supabase Storage
   - Creates ZIP with proper structure
   - Returns (zip_bytes, folder_name)

**Custom Exception**:
```python
class MissingDocumentsError(Exception):
    def __init__(self, missing: List[str]):
        self.missing = missing
```

### 4. Storage & Repository Extensions

**New Methods**:
- `storage.delete_file(path)`: Delete file from Supabase Storage
- `repository.get_client_documents(client_id)`: Get all documents (no pagination)
- `repository.delete_document(document_id)`: Delete document record

---

## Frontend Implementation

### 1. CreateClientModal Updates

**New Features**:
- Added "Número de Pasaporte o NIE" required field
- Document type dropdown for each uploaded file (Tasa, Pasaporte/NIE, or unclassified)
- Sends `document_types` as JSON array aligned with files

**UI Structure**:
```tsx
interface FileWithType {
  file: File
  documentType: 'TASA' | 'PASSPORT_NIE' | null
}
```

**Form Fields**:
```tsx
formData: {
  full_name: string
  phone_number: string
  passport_or_nie: string  // NEW
  profile_type: string
  notes?: string
}
```

### 2. API Client Updates

**File**: `frontend/src/lib/api.ts`

**Updated Methods**:
```typescript
createClient(
  clientData: CreateClientRequest,
  files?: File[],
  documentTypes?: (string | null)[]
): Promise<Client>

updateClient(
  clientId: string,
  clientData: Partial<CreateClientRequest>,
  files?: File[],
  documentTypes?: (string | null)[]
): Promise<Client>

// NEW
generateExpediente(clientId: string): Promise<{ blob: Blob; filename: string }>
```

**generateExpediente Implementation**:
- Makes POST request to `/clients/{id}/expediente`
- Parses filename from `Content-Disposition` header
- Returns blob and filename for download

### 3. Clients Table Updates

**New Features**:
- Added "📦 Expediente" button in Actions column
- Shows loading state ("⏳ Generando...") during generation
- Auto-downloads ZIP file on success
- Shows alert on error with missing documents

**Button Logic**:
```typescript
const handleGenerateExpediente = async (e, clientId) => {
  const { blob, filename } = await api.generateExpediente(clientId)
  
  // Create download link
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  
  // Cleanup
  window.URL.revokeObjectURL(url)
}
```

---

## Usage Workflow

### Creating a Client with Documents

1. **Click "Crear Cliente"** button on Clients page
2. **Fill required fields**:
   - Name, phone, **passport/NIE** (required)
   - Profile type, notes (optional)
3. **Upload documents**:
   - Select PDF files
   - Choose document type from dropdown for each file
   - Options: "Tasa", "Pasaporte/NIE", or "Sin clasificar (opcional)"
4. **Submit**: Client is created with classified documents

### Generating Expediente

1. **Navigate to Clients page**
2. **Locate client** in table
3. **Click "📦 Expediente"** button
4. **System validates**:
   - Client has `passport_or_nie` field
   - Both TASA and PASSPORT_NIE documents exist
5. **On success**: ZIP downloads automatically
6. **On error**: Alert shows missing requirements

### Error Scenarios

**Missing passport_or_nie**:
```
Alert: "Missing required documents: passport_or_nie field"
```

**Missing documents**:
```
Alert: "Missing documents: TASA, PASSPORT_NIE
Cannot generate expediente. Please upload all required documents (TASA and PASSPORT_NIE)."
```

---

## Technical Details

### NIE Detection Regex
```regex
^[XYZxyz]\d{7}[A-Za-z]$
```

**Explanation**:
- Starts with X, Y, or Z (case insensitive)
- Followed by exactly 7 digits
- Ends with one letter (check digit)

**Examples**:
- Valid: `X1234567A`, `y7654321B`, `Z0000000C`
- Invalid: `12345678A`, `A1234567B`, `X123456A`

### Name Sanitization Logic
```python
def sanitize_name(name: str) -> str:
    sanitized = name.replace(" ", "_")
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', sanitized)
    return sanitized.lower()
```

**Examples**:
- "Juan Pérez García" → "juan_perez_garca"
- "María José López-Sánchez" → "mara_jos_lpez-snchez"

### ZIP Generation Process

1. **Validation**:
   - Check client exists
   - Check `passport_or_nie` field present
   - Verify both TASA and PASSPORT_NIE documents exist

2. **Document Retrieval**:
   - Download TASA PDF from Supabase Storage
   - Download PASSPORT_NIE PDF from Supabase Storage
   - Uses SERVICE_ROLE_KEY for direct storage access

3. **ZIP Creation**:
   - Create in-memory ZIP buffer
   - Create folder: `{sanitized_name}_{uuid[:8]}/`
   - Add files with renamed filenames
   - Return ZIP bytes + folder name

4. **Response**:
   - Stream ZIP as `application/zip`
   - Set `Content-Disposition: attachment; filename={folder}.zip`

---

## Testing Checklist

### Backend Tests
- [ ] `test_sanitize_name()`: Various name formats
- [ ] `test_detect_nie()`: Valid/invalid NIE formats
- [ ] `test_generate_expediente_zip()`: Full ZIP generation
- [ ] `test_expediente_missing_passport()`: 400 error
- [ ] `test_expediente_missing_tasa()`: 400 error
- [ ] `test_expediente_missing_nie_doc()`: 400 error
- [ ] `test_document_upsert()`: Replaces existing doc of same type

### Frontend Tests
- [ ] passport_or_nie field validation
- [ ] Document type selection UI
- [ ] Expediente button click
- [ ] ZIP download trigger
- [ ] Error alert display
- [ ] Loading state during generation

### Integration Tests
- [ ] Create client with classified documents
- [ ] Upload TASA document
- [ ] Upload PASSPORT_NIE document
- [ ] Generate expediente successfully
- [ ] Verify ZIP structure and content
- [ ] Test NIE vs Pasaporte naming
- [ ] Test document replacement (upsert)

---

## Migration Guide for Production

### Step 1: Run Database Migrations
```bash
cd backend
psql -h <supabase-host> -U postgres -d postgres < app/db/migrations/001_add_passport_or_nie.sql
psql -h <supabase-host> -U postgres -d postgres < app/db/migrations/002_add_document_type.sql
```

### Step 2: Update Existing Clients
```sql
-- Set default passport_or_nie for existing clients (temporary)
UPDATE clients
SET passport_or_nie = 'PENDING'
WHERE passport_or_nie IS NULL;
```

### Step 3: Classify Existing Documents
```sql
-- Manually classify existing documents or leave untyped
-- Option 1: Leave untyped (document_type = NULL)
-- Option 2: Manually update based on filename patterns
UPDATE documents
SET document_type = 'TASA'
WHERE original_filename ILIKE '%tasa%';

UPDATE documents
SET document_type = 'PASSPORT_NIE'
WHERE original_filename ILIKE '%passport%' OR original_filename ILIKE '%nie%';
```

### Step 4: Deploy Backend
```bash
# Deploy updated backend with new endpoints and service
# Ensure all dependencies are installed
pip install -r requirements.txt
```

### Step 5: Deploy Frontend
```bash
# Build and deploy frontend
cd frontend
npm run build
# Deploy dist/ folder
```

### Step 6: User Communication
- Notify users about new required field (passport_or_nie)
- Explain document type classification
- Demonstrate expediente generation feature

---

## Known Limitations

1. **Document Limit**: Only 2 required documents (TASA + PASSPORT_NIE)
2. **File Format**: Only PDF files supported
3. **File Size**: 10MB limit per file (frontend validation)
4. **NIE Format**: Only Spanish NIE format detected
5. **Single Document Type**: Only one document per type per client (enforced by DB constraint)
6. **No Version History**: Replacing a document deletes the old one permanently

---

## Future Enhancements

1. **Additional Document Types**:
   - Add more document classifications (e.g., BIRTH_CERTIFICATE, PROOF_OF_ADDRESS)
   - Support for multi-document expedientes

2. **Document Versions**:
   - Keep history of replaced documents
   - Allow viewing previous versions

3. **Batch Operations**:
   - Generate expedientes for multiple clients
   - Bulk document uploads

4. **Email Integration**:
   - Email expediente to client
   - Email to case manager

5. **Template Customization**:
   - Allow customizing folder/file naming patterns
   - Support for different expediente types

6. **Multi-language Support**:
   - Support for non-Spanish passports
   - Detect passport country codes

---

## Support & Troubleshooting

### Common Issues

**Issue**: "Missing required documents" error
- **Solution**: Ensure both TASA and PASSPORT_NIE documents are uploaded with correct types

**Issue**: ZIP file is empty or corrupted
- **Solution**: Check Supabase Storage permissions (SERVICE_ROLE_KEY must have read access)

**Issue**: Document type not saving
- **Solution**: Ensure `document_types` JSON array is properly formatted and aligned with files array

**Issue**: NIE not detected correctly
- **Solution**: Verify NIE format matches regex `^[XYZxyz]\d{7}[A-Za-z]$`

### Debug Commands

**Check client documents**:
```sql
SELECT d.*, dt.document_type
FROM documents d
LEFT JOIN document_types dt ON d.document_type = dt.document_type
WHERE d.client_id = '<uuid>';
```

**Check passport_or_nie field**:
```sql
SELECT id, name, passport_or_nie
FROM clients
WHERE passport_or_nie IS NULL OR passport_or_nie = 'PENDING';
```

---

## Contributors

- Implementation: GitHub Copilot & Development Team
- Feature Design: Based on user requirements for document management and expediente generation
- Testing: Pending full test suite implementation

---

## Version History

- **v1.0.0** (Current): Initial implementation
  - Database schema with document_type enum
  - passport_or_nie field for clients
  - Document classification system
  - Expediente ZIP generation service
  - Frontend UI for client creation and expediente download
