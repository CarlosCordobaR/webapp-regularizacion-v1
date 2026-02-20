# Supabase Integration Quick Reference

## Files Created/Modified

### Schema & Database
- ✅ `backend/app/db/schema.sql` - Enhanced with:
  - `dedupe_key` column in conversations (unique, for idempotency)
  - `storage_path` unique constraint in documents
  - `sync_mappings` table for tracking mock→Supabase ID mappings
  - Updated RLS policies

### Supabase Client
- ✅ `backend/app/db/supabase.py` - Enhanced with:
  - `upsert_client()` - Create or update client by phone_number
  - `upsert_conversation()` - Create conversation with dedupe_key idempotency
  - `upsert_document()` - Create document with storage_path idempotency
  - `upload_file_to_storage()` - Upload with existence check
  - `file_exists_in_storage()` - Check if file already uploaded
  - `ensure_bucket_exists()` - Validate storage bucket setup
  - `generate_dedupe_key()` - SHA256 hash for conversation deduplication
  - `create_sync_mapping()` - Record mock→Supabase ID mappings

### Sync Scripts
- ✅ `backend/app/scripts/sync_mock_to_supabase.py` - Main sync pipeline:
  - Idempotent sync of clients, conversations, documents, files
  - Generates JSON reports in `backend/reports/`
  - Tracks inserted/updated/skipped counts
  - Handles errors gracefully

- ✅ `backend/app/scripts/create_supabase_users.py` - Auth user creation:
  - Creates 5 test users via Supabase Admin API
  - Idempotent (skips existing users)
  - DEV credentials only (not for production)

### Configuration
- ✅ `backend/.env.example` - Added Supabase variables:
  - SUPABASE_URL
  - SUPABASE_ANON_KEY
  - SUPABASE_SERVICE_ROLE_KEY
  - STORAGE_BUCKET

### Documentation
- ✅ `README.md` - Added comprehensive "Syncing Mock Data to Supabase" section
- ✅ `backend/reports/.gitkeep` - Reports directory placeholder

### Tests
- ✅ `backend/app/tests/test_sync_integration.py` - Integration tests:
  - Opt-in via `ENABLE_INTEGRATION_TESTS=1`
  - Tests upsert idempotency
  - Tests dedupe key generation
  - Tests bucket existence checks

---

## Usage Flow

### 1. One-Time Supabase Setup
```bash
# 1. Create Supabase project at https://supabase.com
# 2. Go to SQL Editor, run: backend/app/db/schema.sql
# 3. Go to Storage, create bucket: "client-documents"
# 4. Copy credentials to backend/.env
```

### 2. Create Test Users
```bash
cd backend
python -m app.scripts.create_supabase_users
```

### 3. Sync Mock Data
```bash
cd backend
python -m app.scripts.sync_mock_to_supabase
```

### 4. Switch to Production Mode
```bash
# backend/.env
APP_MODE=real
STORAGE_MODE=supabase
DB_MODE=supabase

# frontend/.env
VITE_APP_MODE=real
```

### 5. Verify
```bash
# Start backend
uvicorn app.main:app --reload

# Start frontend (new terminal)
cd frontend && npm run dev

# Login with: admin@local.test / Admin123!
```

---

## Idempotency Guarantees

| Entity | Unique Key | Behavior on Re-run |
|--------|-----------|-------------------|
| Clients | `phone_number` | Updates existing if found |
| Conversations | `dedupe_key` (SHA256) | Skips if already exists |
| Documents | `storage_path` | Skips if already exists |
| Files | Storage path lookup | Skips if already uploaded |

**Safe to run multiple times** - no duplicates created.

---

## Troubleshooting

### "Storage bucket does not exist"
```bash
# Solution: Create bucket manually in Supabase Dashboard → Storage
# Bucket name: client-documents
# Public or Private: Your choice (public for MVP)
```

### "Missing SUPABASE_SERVICE_ROLE_KEY"
```bash
# Solution: Add to backend/.env
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

### "Local file not found"
```bash
# Solution: Ensure mock DB is seeded first
cd backend
APP_MODE=mock uvicorn app.main:app --reload
# Wait for seed, then Ctrl+C
python -m app.scripts.sync_mock_to_supabase
```

### "User creation failed"
```bash
# Check: Is SUPABASE_SERVICE_ROLE_KEY correct?
# Check: Does your Supabase plan support Admin API?
# Fallback: Create users manually in Supabase Dashboard → Authentication
```

---

## Test Users (DEV Only)

| Email | Password | Role |
|-------|----------|------|
| admin@local.test | Admin123! | admin |
| ops1@local.test | Ops123! | operations |
| ops2@local.test | Ops123! | operations |
| reviewer@local.test | Review123! | reviewer |
| readonly@local.test | Read123! | readonly |

⚠️ **DO NOT USE IN PRODUCTION**

---

## Running Integration Tests

```bash
cd backend

# Export Supabase credentials
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=your-key
export STORAGE_BUCKET=client-documents
export ENABLE_INTEGRATION_TESTS=1

# Run tests
pytest app/tests/test_sync_integration.py -v
```

Tests verify:
- Client upsert creates and updates correctly
- Dedupe key generation is deterministic
- Conversation upsert respects dedupe_key
- Storage bucket exists

---

## Implementation Notes

### Assumptions & Defaults

1. **Storage Path Format**: 
   - Mock: `profiles/{profile_type}/{client_name}_{client_id}/{timestamp}_{filename}.pdf`
   - Same format preserved in Supabase Storage

2. **Dedupe Key Algorithm**:
   - `SHA256(client_id|direction|created_at|message_type|content)`
   - Truncated to 64 chars to fit VARCHAR(64) column

3. **Mock Database Location**:
   - `backend/.local_storage/mock_db.sqlite`
   - `backend/.local_storage/files/` for PDFs

4. **Supabase RLS**:
   - Simple policies: all authenticated users can read/write
   - Service role bypasses RLS for sync operations
   - Enhance in production with row-level permissions

5. **Error Handling**:
   - Sync continues on individual item errors
   - All errors logged and included in report
   - Script exits 0 even with partial failures (check report JSON)

6. **Conversation Direction**:
   - Schema supports both `INBOUND`/`OUTBOUND` and `inbound`/`outbound`
   - Sync preserves original casing from mock data

---

## Next Steps

1. ✅ Run sync to populate Supabase with mock dataset
2. ✅ Test in production mode with real Supabase
3. 🔲 Configure WhatsApp Business API for real webhooks
4. 🔲 Deploy backend to production (Railway/Render/Fly.io)
5. 🔲 Deploy frontend to production (Vercel/Netlify)
6. 🔲 Enhance RLS policies for production security
7. 🔲 Set up monitoring and error tracking

---

## Support

- See [README.md](../README.md) for full setup instructions
- See [MOCK_MODE.md](../MOCK_MODE.md) for mock mode details
- Check `backend/reports/` for sync reports
- Review Supabase Dashboard for data verification
