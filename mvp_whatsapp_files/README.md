# WhatsApp Business Cloud API → Supabase MVP

A minimal, production-lean webapp that ingests WhatsApp Business Cloud API webhooks, stores conversations + PDFs in Supabase (Postgres + Storage), and exposes an internal web panel (React) to review clients, conversations, and documents.

## 🚀 Quick Start (Mock Mode)

**Want to try it without any external dependencies?** Use mock mode for instant local development:

```bash
# Backend
cd backend
cp .env.example .env
# Set APP_MODE=mock in .env
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
cp .env.example .env
# Set VITE_APP_MODE=mock in .env
npm install
npm run dev
```

Login at [http://localhost:5173](http://localhost:5173) with any of the 5 mock users (click to login, no password needed).

👉 **See [MOCK_MODE.md](MOCK_MODE.md) for complete documentation on mock mode, test data, and syncing to production.**

---

## 🧪 Supabase Validation Mode (No WhatsApp)

**Want to validate the MVP end-to-end against REAL Supabase without WhatsApp integration?** Use validation mode to test the full stack with Supabase Postgres, Storage, and Auth before connecting WhatsApp.

### What This Mode Enables

- ✅ Manual client creation from frontend
- ✅ Document uploads (TASA, PASSPORT_NIE) to Supabase Storage
- ✅ Simulated conversations via dev endpoints (test UI timeline)
- ✅ Seed script for deterministic test dataset (10 clients)
- ✅ Full Supabase integration (Postgres + Storage + Auth)
- ❌ **No WhatsApp API required**

### Step-by-Step Setup

#### 1. Configure Supabase

Create your Supabase project if you haven't already, then:

**A. Run Database Schema**
```sql
-- In Supabase SQL Editor, run:
-- backend/app/db/schema.sql
-- Creates: clients, conversations, documents, sync_mappings tables
```

**B. Create Storage Bucket**
```bash
# In Supabase Dashboard → Storage:
# 1. Click "New bucket"
# 2. Name: client-documents
# 3. Privacy: PRIVATE (recommended) or PUBLIC
#    - Private: requires signed URLs (more secure)
#    - Public: direct access (simpler for MVP testing)
```

**C. Create Test User**
```bash
# In Supabase Dashboard → Authentication → Users:
# Click "Add User" → Email + Password
# Example: test@example.com / TestPassword123!
```

**D. (Optional) Create Row Level Security Policies**
```sql
-- If using private bucket, add RLS policies:
-- See backend/app/db/schema.sql lines 125-169
-- For now, you can keep RLS disabled for testing
```

#### 2. Backend Configuration

```bash
cd backend

# Copy env file
cp .env.example .env

# Edit .env with these settings:
APP_MODE=real
WHATSAPP_ENABLED=false          # ← Disable WhatsApp
DEV_ENDPOINTS_ENABLED=true      # ← Enable dev endpoints
DEV_TOKEN=my-secret-dev-token   # ← Set a secure token
STORAGE_PUBLIC=false            # ← Use signed URLs (recommended)

# Supabase credentials (from Supabase Dashboard → Settings → API)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...  # From "Project API keys → anon public"
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # From "Project API keys → service_role"
STORAGE_BUCKET=client-documents

# Prisma database URL (from Supabase Dashboard → Settings → Database → Connection string)
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres?schema=public
DIRECT_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres

# Install dependencies
pip install -e .
pip install reportlab  # For generating test PDFs

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected startup output:**
```
INFO: Starting application in real mode
INFO: DB mode: supabase, Storage mode: supabase
INFO: Dev endpoints enabled at /dev/*
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

#### 3. Frontend Configuration

```bash
cd frontend

# Copy env file
cp .env.example .env

# Edit .env:
VITE_APP_MODE=real
VITE_API_BASE_URL=http://localhost:8000
VITE_DEV_ENDPOINTS_ENABLED=true  # Shows dev tools panel
VITE_DEV_TOKEN=my-secret-dev-token  # Must match backend

# Supabase credentials (same as backend)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGc...

# Install and start
npm install
npm run dev
```

Frontend runs at [http://localhost:5173](http://localhost:5173)

#### 4. Seed Test Dataset

Use the `/dev/seed` endpoint to create 10 test clients with conversations and documents:

```bash
# Using curl:
curl -X POST http://localhost:8000/dev/seed \
  -H "X-Dev-Token: my-secret-dev-token"

# Expected response:
{
  "clients_created": 10,
  "conversations_created": 30,
  "documents_created": 15,
  "message": "Successfully seeded 10 clients with conversations and documents"
}
```

**What gets created:**
- 10 clients with different profile types (ASYLUM, ARRAIGO, STUDENT, etc.)
- 2-4 conversations per client (mix of inbound/outbound)
- 1-2 documents per client (TASA and/or PASSPORT_NIE PDFs)
- All seeded data marked with `[SEED]` prefix in notes for easy identification

#### 5. Validate the UI

**A. Login**
- Go to http://localhost:5173
- Login with test@example.com (user created in step 1C)

**B. Verify Clients**
- Should see 10 clients in the list
- Click on any client to see details

**C. Test Document Downloads**
- In client detail page, click on a document
- Should get a signed URL and PDF downloads successfully

**D. Test Conversation Timeline**
- Scroll down to "Conversaciones" section
- Should see 2-4 messages per client with inbound/outbound indicators

**E. Create Test Conversation** (via dev endpoint)
```bash
# Get a client_id from the UI, then:
curl -X POST http://localhost:8000/dev/conversations \
  -H "X-Dev-Token: my-secret-dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "uuid-from-ui",
    "direction": "inbound",
    "message_text": "Hola, necesito información sobre arraigo",
    "message_type": "text"
  }'

# Refresh client detail page → new message appears
```

**F. Upload Document** (via frontend)
- Click "Upload Document" button
- Select document type (TASA or PASSPORT_NIE)
- Choose a PDF file
- Upload → appears in documents list

**G. Upload Document** (via dev endpoint)
```bash
curl -X POST http://localhost:8000/dev/documents/upload \
  -H "X-Dev-Token: my-secret-dev-token" \
  -F "client_id=uuid-from-ui" \
  -F "document_type=TASA" \
  -F "file=@/path/to/test.pdf"
```

#### 6. (Optional) Run Integration Tests

```bash
cd backend

# Set test environment
export RUN_SUPABASE_INTEGRATION_TESTS=true
export APP_MODE=real
export DEV_ENDPOINTS_ENABLED=true
export DEV_TOKEN=my-secret-dev-token

# Run tests
pytest app/tests/test_supabase_validation.py -v

# Expected: 10+ tests pass
```

### Dev Endpoints Reference

All dev endpoints require `X-Dev-Token` header. Available when `DEV_ENDPOINTS_ENABLED=true`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/dev/seed` | POST | Create 10 test clients + conversations + documents |
| `/dev/conversations` | POST | Create a test conversation without WhatsApp |
| `/dev/documents/upload` | POST | Upload a document without WhatsApp |
| `/dev/reset` | DELETE | Delete all seeded data (clients with `[SEED]` notes) |

**Example: Create conversation**
```json
POST /dev/conversations
{
  "client_id": "uuid",
  "direction": "inbound",  // or "outbound"
  "message_text": "Test message",
  "message_type": "text"
}
```

### Troubleshooting

**Error: "Missing required environment variables: SUPABASE_URL"**
- **Fix**: Ensure `.env` has `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` set

**Error: "pydantic_core.ValidationError: database_url Extra inputs are not permitted"**
- **Fix**: Already fixed in `backend/app/core/config.py` with `extra = "ignore"`

**Error: "Storage bucket 'client-documents' not found"**
- **Fix**: Create bucket in Supabase Dashboard → Storage → New Bucket

**Error: "Row Level Security policy violation"**
- **Fix**: Either disable RLS for testing OR uncomment RLS policies in `schema.sql`

**Signed URLs return 403**
- **Fix**: Ensure `STORAGE_PUBLIC=false` and bucket is private, OR set `STORAGE_PUBLIC=true` and make bucket public

**Documents not downloading**
- **Check**: Bucket permissions in Supabase Dashboard → Storage → `client-documents` → Policies
- **Check**: Backend logs for storage errors (`uvicorn` terminal)

**Frontend can't connect to backend**
- **Check**: Backend is running on port 8000 (`curl http://localhost:8000/health`)
- **Check**: CORS allows `http://localhost:5173` (already configured in `backend/app/main.py`)

**Seed endpoint returns 401**
- **Fix**: Ensure `X-Dev-Token` header matches `DEV_TOKEN` in backend `.env`

**No conversations showing in UI**
- **Check**: Client detail page should show "Conversaciones (N)" section
- **Fix**: Run `/dev/seed` to create test conversations OR manually create via `/dev/conversations`

### Next Steps After Validation

Once you've validated Supabase integration:

1. **Enable WhatsApp**: Set `WHATSAPP_ENABLED=true` and add WhatsApp credentials
2. **Disable Dev Endpoints**: Set `DEV_ENDPOINTS_ENABLED=false` for production
3. **Enable RLS**: Uncomment RLS policies in `schema.sql` for security
4. **Set up CI/CD**: See [TODO_BACKLOG.md](docs/audit/TODO_BACKLOG.md) for production checklist
5. **Add webhook signature verification**: See audit P0-2 in TODO_BACKLOG.md

---

## Assumptions & Defaults

1. **Supabase Setup**: Assumes you have a Supabase project already created with:
   - Project URL and anon key available
   - Service role key available for backend operations
   - Storage bucket named `client-documents` will be created (public read for MVP simplicity)
   - RLS disabled for MVP or simple policies for authenticated users only

2. **WhatsApp Business API**: Assumes you have:
   - A Meta Business Account with WhatsApp Business API access
   - Phone Number ID and Business Account ID
   - Permanent access token (WHATSAPP_TOKEN)
   - Webhook VERIFY_TOKEN of your choice

3. **Profile Classification**: Simple keyword-based rules (no LLM):
   - "asilo" → ASYLUM
   - "arraigo" → ARRAIGO
   - "estudiante" → STUDENT
   - "irregular" → IRREGULAR
   - else → OTHER

4. **Storage Strategy**: Public bucket for MVP simplicity
   - Path format: `profiles/{profile_type}/{client_name}_{client_id}/{timestamp}_{filename}.pdf`
   - If you need private bucket, uncomment signed URL endpoint

5. **Auth**: Supabase Auth with email/password for internal users
   - Users must be created manually in Supabase dashboard for MVP

6. **Media Types**: MVP handles PDF documents and generic media attachments
   - Only stores media with mime type or file extension

7. **Error Handling**: Basic retry logic for media download (3 attempts)

8. **Pagination**: Default page size of 50 for all list endpoints

9. **Time Zone**: All timestamps stored in UTC

10. **Local Development**: Backend runs on port 8000, frontend on port 5173

11. **Mock Mode Available**: Complete local development mode with deterministic test data
   - No external dependencies required (no Supabase, no WhatsApp API)
   - 10 pre-seeded clients with realistic Spanish immigration data
   - 5 mock users for authentication testing
   - Local SQLite database and filesystem storage
   - See [MOCK_MODE.md](MOCK_MODE.md) for details

12. **Supabase Validation Mode**: Test Supabase integration without WhatsApp
   - Set `WHATSAPP_ENABLED=false` to skip WhatsApp requirements
   - Set `DEV_ENDPOINTS_ENABLED=true` to enable test endpoints
   - Use `/dev/seed` to create test dataset (10 clients + conversations + documents)
   - Use `/dev/conversations` and `/dev/documents/upload` to test without WhatsApp
   - All dev endpoints protected by `DEV_TOKEN` header
   - See "Supabase Validation Mode" section above for complete guide

## Implementation Checklist

- [x] Create project structure
- [x] Create database schema (schema.sql)
- [x] Create backend core (config, logging)
- [x] Create backend models & DB layer
- [x] Add mock mode for local development (adapters pattern)
- [x] Add mock authentication for frontend
- [x] Add sync script for mock to production migration
- [x] Create WhatsApp integration (webhook, client, media, verify)
- [x] Create backend services (classifier, ingest, storage)
- [x] Create backend API endpoints
- [x] Create backend tests
- [x] Create frontend React app
- [x] Create configuration files
- [x] Document local setup & run instructions

## Tech Stack

**Backend:**
- FastAPI + Uvicorn
- httpx (HTTP client)
- pydantic (validation)
- supabase-py
- pytest (testing)

**Frontend:**
- React + TypeScript
- Vite
- Supabase JS client
- Minimal CSS OR Mock Mode (SQLite + Local FS)
- WhatsApp Business Cloud API OR Mock fixtures
- Adapter pattern for seamless mode switching

## Mock Mode vs Production Mode

This application supports two operating modes:

### MOCK_MODE.md              # Mock mode documentation
├── .gitignore
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── core/
│       │   ├── config.py      # Mock mode settings
│       │   └── logging.py
│       ├── adapters/          # NEW: Adapter pattern for mock/real
│       │   ├── repository_base.py
│       │   ├── storage_base.py
│       │   ├── whatsapp_base.py
│       │   ├── factory.py     # Dependency injection
│       │   ├── mock/          # Mock implementations
│       │   │   ├── mock_repository.py
│       │   │   ├── mock_storage.py
│       │   │   ├── mock_whatsapp.py
│       │   │   └── seed.py    # Test data generator
│       │   └── real/          # Production implementations
│       │       ├── supabase_repository.py
│       │       ├── supabase_storage.py
│       │       └── meta_whatsapp.py
│       ├── db/
│       │   ├── supabase.py
│       │   └── schema.sql
│       ├── whatsapp/
│       │   ├── webhook.py
│       │   ├── client.py
│       │   ├── media.py
│       │   └── verify.py
│       ├── services/
│       │   ├── classifier.py
│       │   ├── ingest.py
│       │   └── storage.py
│       ├── api/
│       │   ├── health.py
│       │   ├── clients.py
│       │   ├── documents.py
│       │   └── conversations.py
│       ├── scripts/
│       │   └── sync_to_supabase.py  # Sync mock to production
│       ├── models/
│       │   ├── enums.py
│       │   └── dto.py
│       └── tests/
│           ├── test_health.py
│           └── test_classifier.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    ├── tsconfig.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── lib/
        │   ├── supabase.ts
    Quick Start: Mock Mode (No External Dependencies)

For instant local development without Supabase or WhatsApp API:

```bash
# 1. Backend
cd backend
cp .env.example .env
# Edit .env: Set APP_MODE=mock
pip install -e .
uvicorn app.main:app --reload

# 2. Frontend (new terminal)
cd frontend
cp .env.example .env
# Edit .env: Set VITE_APP_MODE=mock
npm install
npm run dev

# 3. Login at http://localhost:5173
# Click any of the 5 mock users to login (no password needed)
```

See [MOCK_MODE.md](MOCK_MODE.md) for complete mock mode documentation.

---

## 🔄 Syncing Mock Data to Supabase

Want to transition from mock mode to real Supabase with your test dataset? Use the sync pipeline to migrate all 10 mock clients, conversations, and documents to your Supabase instance.

### Prerequisites

1. **Supabase Project Setup**
   - Create project at https://supabase.com
   - Get credentials from Project Settings → API:
     - Project URL
     - Anon key
     - **Service role key** (required for sync)

2. **Run Schema SQL**
   ```bash
   # Go to Supabase Dashboard → SQL Editor
   # Copy and run: backend/app/db/schema.sql
   ```

3. **Create Storage Bucket**
   ```bash
   # Go to Supabase Dashboard → Storage
   # Create bucket: "client-documents"
   # Set as PUBLIC for MVP (or PRIVATE and use signed URLs)
   ```

4. **Set Environment Variables**
   ```bash
   # In backend/.env
   export SUPABASE_URL=https://your-project.supabase.co
   export SUPABASE_ANON_KEY=your-anon-key-here
   export SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
   export STORAGE_BUCKET=client-documents
   ```

### Step 1: Create Auth Users

Create 5 test users in Supabase Auth for development:

```bash
cd backend

# With virtual environment activated
python -m app.scripts.create_supabase_users
```

**Output:**
```
✓ Created:  5
⊙ Skipped:  0 (already exist)
✗ Failed:   0

TEST CREDENTIALS (DEV ONLY):
--------------------------------------------------
admin@local.test          | Admin123!       | admin
ops1@local.test           | Ops123!         | operations
ops2@local.test           | Ops123!         | operations
reviewer@local.test       | Review123!      | reviewer
readonly@local.test       | Read123!        | readonly
--------------------------------------------------
```

⚠️ **These are hardcoded DEV credentials. Do not use in production!**

### Step 2: Sync Mock Dataset

Sync all mock data (clients, conversations, documents, PDFs) to Supabase:

```bash
cd backend

# Ensure mock data exists (run backend once in mock mode to seed)
# APP_MODE=mock uvicorn app.main:app --reload
# Ctrl+C after startup

# Run sync (idempotent - safe to run multiple times)
python -m app.scripts.sync_mock_to_supabase
```

**Expected Output:**
```
==================================================
Starting Mock Data -> Supabase Sync
==================================================
Supabase URL: https://your-project.supabase.co
Storage Bucket: client-documents

=== Syncing Clients ===
Found 10 clients in mock database
Inserted client: Miguel Hernández (+34600000001)
Inserted client: Laura Sánchez (+34600000002)
...
Clients sync complete: 10 inserted, 0 updated, 0 skipped

=== Syncing Conversations ===
Found 8 conversations for client ...
...
Conversations sync complete: 83 inserted, 0 skipped

=== Syncing Documents ===
Found 3 documents for client ...
Uploaded file to storage: profiles/ASYLUM/Miguel_Hernandez_...
...
Documents sync complete: 25 inserted, 0 skipped
Files: 25 uploaded, 0 skipped

==================================================
SYNC COMPLETE
==================================================
Clients: 10 inserted, 0 updated, 0 skipped
Conversations: 83 inserted, 0 skipped
Documents: 25 inserted, 0 skipped
Files: 25 uploaded, 0 skipped

Full report: backend/reports/sync_report_20260211_143022.json
==================================================
```

### Step 3: Switch to Production Mode

Update your environment to use real Supabase:

**Backend (.env):**
```env
APP_MODE=real
STORAGE_MODE=supabase
DB_MODE=supabase

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
STORAGE_BUCKET=client-documents

# WhatsApp (optional, can use mock for now)
WHATSAPP_PHONE_NUMBER_ID=mock
WHATSAPP_ACCESS_TOKEN=mock
WHATSAPP_VERIFY_TOKEN=mock123
```

**Frontend (.env):**
```env
VITE_APP_MODE=real
VITE_API_BASE_URL=http://localhost:8000

VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### Step 4: Verify

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# Start frontend (new terminal)
cd frontend
npm run dev

# Login at http://localhost:5173 with:
# admin@local.test / Admin123!

# You should see all 10 mock clients loaded from Supabase!
```

### Sync Reports

Each sync run generates a detailed JSON report in `backend/reports/`:

```json
{
  "timestamp": "2026-02-11T14:30:22.123456",
  "script": "sync_mock_to_supabase",
  "summary": {
    "clients": {
      "inserted": 10,
      "updated": 0,
      "skipped": 0,
      "total": 10
    },
    "conversations": {
      "inserted": 83,
      "skipped": 0,
      "total": 83
    },
    "documents": {
      "inserted": 25,
      "skipped": 0,
      "total": 25
    },
    "files": {
      "uploaded": 25,
      "skipped": 0,
      "total": 25
    }
  },
  "errors": [],
  "mappings": {
    "clients": {
      "mock-uuid": "supabase-uuid",
      ...
    }
  }
}
```

### Re-running Sync (Idempotency)

The sync script is **idempotent** - safe to run multiple times:

- **Clients**: Matched by `phone_number` (unique). Updates if exists.
- **Conversations**: Matched by `dedupe_key` (SHA256 hash). Skips if exists.
- **Documents**: Matched by `storage_path` (unique). Skips if exists.
- **Files**: Checks if file exists in storage. Skips if exists.

**Example re-run output:**
```
Clients: 0 inserted, 10 updated, 0 skipped
Conversations: 0 inserted, 83 skipped
Documents: 0 inserted, 25 skipped
Files: 0 uploaded, 25 skipped
```

### Troubleshooting

**Error: "Storage bucket 'client-documents' does not exist"**
```
Solution: Create bucket in Supabase Dashboard → Storage
```

**Error: "Missing required environment variables: SUPABASE_SERVICE_ROLE_KEY"**
```
Solution: Export SUPABASE_SERVICE_ROLE_KEY in .env or shell:
export SUPABASE_SERVICE_ROLE_KEY=your-key-here
```

**Error: "Local file not found"**
```
Solution: Ensure mock database has been seeded by running backend once in mock mode:
APP_MODE=mock uvicorn app.main:app --reload
# Let it seed, then Ctrl+C
```

**Some conversations/documents skipped**
```
This is normal on re-runs due to idempotency. Check report JSON for details.
```

---

### Full Setup: Production Mode

###     │   ├── mockAuth.ts     # NEW: Mock authentication
        │   └── api.ts
        ├── pages/
        │   ├── Login.tsx      # Updated for mock mode
        │   ├── Clients.tsx
        │   └── ClientDetail.tsx
        └── components/
            ├── ProtectedRoute.tsx  # Updated for mock mode
│       │   ├── documents.py
│       │   └── conversations.py
│       ├── models/
│       │   ├── enums.py
│       │   └── dto.py
│       └── tests/
│           ├── test_health.py
│           └── test_classifier.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    ├── tsconfig.json
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── lib/
        │   ├── supabase.ts
        │   └── api.ts
        ├── pages/
        │   ├── Login.tsx
        │   ├── Clients.tsx
        │   └── ClientDetail.tsx
        └── components/
            ├── ProtectedRoute.tsx
            ├── ClientTable.tsx
            ├── DocumentList.tsx
            └── ConversationList.tsx
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project (free tier works)
- WhatsApp Business Cloud API credentials
- ngrok (for local webhook testing)

### 1. Supabase Setup

1. Create a Supabase project at https://supabase.com
2. Go to Project Settings → API to get your:
   - Project URL
   - Anon (public) key
   - Service role key
3. Go to Storage → Create bucket:
   - Name: `client-documents`
   - Public bucket: Yes (for MVP simplicity)
4. Execute the schema:
   - Go to SQL Editor
   - Copy contents of `backend/app/db/schema.sql`
   - Run the SQL
5. Create an internal user:
   - Go to Authentication → Users
   - Add user with email/password

### 2. WhatsApp Setup

1. Create a Meta Business Account
2. Set up WhatsApp Business API (Cloud API)
3. Get your Phone Number ID and permanent access token
4. Configure webhook URL (will use ngrok for local dev)

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Copy environment template
cp ../.env.example .env

# Edit .env with your credentials
# IMPORTANT: Fill in all values

# Verify setup
python -m pytest app/tests/

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template (if needed)
# Frontend will read from backend URL

### Mock Mode (Minimal Configuration)

**Backend (.env):**
```env
APP_MODE=mock
MOCK_SEED_ON_START=true
STORAGE_MODE=local
DB_MODE=sqlite
```

**Frontend (.env):**
```env
VITE_APP_MODE=mock
VITE_API_BASE_URL=http://localhost:8000
```

### Production Mode (Full Configuration)

# Run development server
npm run dev
```

Frontend will be available at http://localhost:5173

### 5. Local Webhook Testing

# Mode Configuration
APP_MODE=real  # 'mock' or 'real'
STORAGE_MODE=supabase  # 'local' or 'supabase'
DB_MODE=supabase  # 'sqlite', 'postgres', or 'supabase'

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# WhatsApp
WHATSAPP_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
# Mode
VITE_APP_MODE=real  # 'mock' or 'real'

# API
VITE_API_BASE_URL=http://localhost:8000

# Supabase (for production auth)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
# Storageo/webhook
# Verify Token: (your VERIFY_TOKEN from .env)

# Test webhook verification
curl "http://localhost:8000/webhook?hub.mode=subscribe&hub.verify_token=YOUR_VERIFY_TOKEN&hub.challenge=test123"
# Should return: test123

# Test webhook POST (sample text message)
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "id": "BUSINESS_ACCOUNT_ID",
      "changes": [{
        "value": {
          "messaging_product": "whatsapp",
          "metadata": {
            "display_phone_number": "1234567890",
            "phone_number_id": "PHONE_NUMBER_ID"
          },
          "contacts": [{
            "profile": {
              "name": "John Doe"
            },
            "wa_id": "1234567890"
          }],
          "messages": [{
            "from": "1234567890",
            "id": "wamid.test123",
            "timestamp": "1234567890",document

### Mock Mode Only
- `GET /mock-storage/{path}` - Direct file download (mock mode)
- `POST /mock-auth/login` - Mock user authentication
- `GET /mock-auth/session` - Get current mock session
- `POST /mock-auth/logout` - Sign out mock user
- `GET /mock-auth/users` - List all mock users
            "text": {
              "body": "Necesito ayuda con mi proceso de asilo"
            },
            "type": "text"
          }]
        },
        "field": "messages"
      }]
   Migrating from Mock to Production

Developed locally with mock data and ready to deploy? Sync your data to Supabase:

```bash
# 1. Configure real Supabase credentials in .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key

# 2. Run sync script
cd backend
python -m app.scripts.sync_to_supabase
```

This will:
- Create all clients in Supabase with new UUIDs
- Migrate all conversations with proper client linkage
- Upload all files to Supabase Storage
- Create document records with correct paths

See [MOCK_MODE.md](MOCK_MODE.md) for detailed migration guide.

##  }]
  }'
```

### 6. Using Docker Compose (Optional)

```bash
# Start both backend and frontend
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Environment Variables

See `.env.example` for all required variables:

**Backend (.env in backend/ directory):**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
WHATSAPP_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_BUSINESS_ACCOUNT_ID=your-business-account-id
VERIFY_TOKEN=your-custom-verify-token
APP_BASE_URL=http://localhost:8000
STORAGE_BUCKET=client-documents
```

**Frontend (optional .env in frontend/ directory):**
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_BASE_URL=http://localhost:8000
```

## API Endpoints

### Health
- `GET /health` - Health check

### Webhook
- `GET /webhook` - WhatsApp webhook verification
- `POST /webhook` - WhatsApp webhook handler

### Clients
- `GET /clients?page=1&page_size=50` - List clients
- `GET /clients/{client_id}` - Get client details
- `GET /clients/{client_id}/conversations?page=1&page_size=50` - Get client conversations
- `GET /clients/{client_id}/documents?page=1&page_size=50` - Get client documents
- `POST /clients` - Create a new client

### Documents
- `GET /documents/{document_id}/signed-url` - Get signed URL for private document (optional)

## Crear Cliente desde la Webapp

La aplicación permite crear nuevos clientes manualmente desde el panel web.

### Funcionalidad

**Ubicación:** Página de clientes (/clients)
**Botón:** "Crear Cliente" (esquina superior derecha)

### Formulario de Creación

El modal solicita los siguientes campos:

1. **Nombre completo** (obligatorio)
   - Texto libre, máximo 255 caracteres
   - Se eliminarán espacios en blanco al inicio/final

2. **Teléfono** (obligatorio, único)
   - Formato: 8-15 dígitos, opcionalmente con prefijo '+'
   - Ejemplo válido: `+34600111222`, `34600111222`, `600111222`
   - El sistema normaliza automáticamente (elimina espacios, guiones, paréntesis)

3. **Tipo de perfil** (opcional, default: OTHER)
   - Opciones: ASYLUM, ARRAIGO, STUDENT, IRREGULAR, OTHER

4. **Notas** (opcional)
   - Campo de texto libre para información adicional
   - Máximo 1000 caracteres

### Validación

**Frontend:**
- Nombre no puede estar vacío
- Teléfono debe contener 8-15 dígitos
- Formato de teléfono: `/^\+?\d{8,15}$/`

**Backend:**
- Validación de formato de teléfono con Pydantic
- Verificación de número duplicado (retorna 409 Conflict)
- Normalización automática (eliminación de espacios y caracteres especiales)

### Comportamiento

**Éxito (201 Created):**
- Modal se cierra automáticamente
- Lista de clientes se refresca
- Mensaje de éxito: "Cliente creado exitosamente"
- Nuevo cliente aparece en la lista

**Errores:**
- **400 Bad Request:** Formato de teléfono inválido
- **409 Conflict:** Número de teléfono ya existe
- **500 Internal Server Error:** Error del servidor

### Ejemplo de Uso (curl)

```bash
# Crear cliente básico
curl -X POST http://localhost:8000/clients \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Juan Pérez García",
    "phone_number": "+34600111222",
    "profile_type": "ARRAIGO"
  }'

# Crear cliente con notas
curl -X POST http://localhost:8000/clients \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "María López",
    "phone_number": "+34611222333",
    "profile_type": "STUDENT",
    "status": "active",
    "notes": "Referido por cliente existente"
  }'

# Respuesta exitosa (201)
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Juan Pérez García",
  "phone_number": "+34600111222",
  "profile_type": "ARRAIGO",
  "status": "active",
  "metadata": {},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}

# Error: número duplicado (409)
{
  "detail": "Phone number +34600111222 already exists"
}

# Error: formato inválido (422)
{
  "detail": [
    {
      "loc": ["body", "phone_number"],
      "msg": "Invalid phone number format. Must contain 8-15 digits, optionally starting with '+' (e.g., +34600111222)",
      "type": "value_error"
    }
  ]
}
```

### Arquitectura

**Backend-First Approach:**
- El frontend NO inserta directamente en Supabase
- Todas las creaciones pasan por el endpoint POST /clients
- Backend usa SERVICE_ROLE_KEY para operaciones de escritura
- Centraliza validación y lógica de negocio

**Componentes:**
- `backend/app/api/clients.py` - Endpoint POST /clients
- `backend/app/models/dto.py` - ClientCreateRequest, validate_phone_number()
- `backend/app/db/supabase.py` - create_client() con manejo de duplicados
- `frontend/src/components/CreateClientModal.tsx` - Modal de creación
- `frontend/src/lib/api.ts` - createClient() API wrapper

**Tests:**
- `backend/app/tests/test_clients_create.py` - Suite completa de tests
  - Creación exitosa
  - Manejo de duplicados (409)
  - Validación de formato (400)
  - Normalización de teléfono
  - Valores por defecto



## Frontend Routes

- `/` - Login page (redirects to /clients if authenticated)
- `/clients` - List all clients
- `/clients/:id` - Client detail with conversations and documents

## Testing

```bash
cd backend
source venv/bin/activate
python -m pytest app/tests/ -v
```

## Deployment Considerations

For production deployment:

1. **Backend:**
   - Deploy to service like Railway, Render, or Fly.io
   - Set environment variables
   - Use production ASGI server (uvicorn with workers)

2. **Frontend:**
   - Build: `npm run build`
   - Deploy static files to Vercel, Netlify, or Cloudflare Pages
   - Set VITE_API_BASE_URL to production backend URL

3. **Supabase:**
   - Enable RLS policies for production
   - Create proper indexes
   - Set up backup strategy

4. **WhatsApp:**
   - Update webhook URL to production backend
   - Enable webhook signature verification

5. **Monitoring:**
   - Add structured logging
   - Set up error tracking (Sentry)
   - Monitor webhook delivery

## Troubleshooting

**Webhook not receiving messages:**
- Check ngrok is running and URL is correct in Meta Dashboard
- Verify VERIFY_TOKEN matches
- Check backend logs for errors

**Media download failing:**
- Verify WHATSAPP_TOKEN is valid and has required permissions
- Check network connectivity
- Ensure Supabase Storage bucket exists and is accessible

**Frontend auth issues:**
- Verify Supabase credentials in frontend
- Check user exists in Supabase Auth
- Clear browser cache/cookies

**Database connection errors:**
- Verify Supabase credentials
- Check if schema is properly created
- Ensure service role key is used for backend operations

## License

MIT
