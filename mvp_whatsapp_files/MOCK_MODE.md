# Mock Mode Documentation

Complete guide for running the WhatsApp Client Manager in mock mode for local development without external dependencies.

## Overview

Mock mode allows you to develop and test the full application stack locally without needing:
- Real WhatsApp Business API credentials
- Supabase database and storage
- External services or API keys

Everything runs with deterministic test data that you can reset and modify as needed.

---

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Copy environment template
cp .env.example .env

# Configure mock mode in .env
APP_MODE=mock
MOCK_SEED_ON_START=true
STORAGE_MODE=local
DB_MODE=sqlite

# Install dependencies
pip install -r requirements.txt

# Start backend (will auto-seed mock data on startup)
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Copy environment template
cp .env.example .env

# Configure mock mode in .env
VITE_APP_MODE=mock
VITE_API_BASE_URL=http://localhost:8000

# Install dependencies
npm install

# Start frontend
npm run dev
```

Frontend will be available at `http://localhost:5173`

### 3. Login with Mock Users

Navigate to `http://localhost:5173/login` and either:

**Quick Login** - Click any predefined user:
- Admin User (`admin@mock.local`)
- María García (`lawyer1@mock.local`) 
- Carlos Rodríguez (`lawyer2@mock.local`)
- Ana López (`assistant1@mock.local`)
- Guest Viewer (`viewer@mock.local`)

**Manual Entry** - Enter any mock user email (no password required in mock mode)

---

## Mock Data

### Clients (10 total)

Mock database is seeded with 10 clients distributed across profile types:

| Name | Phone | Profile Type | Messages | Documents |
|------|-------|--------------|----------|-----------|
| Miguel Hernández | +34600000001 | ASYLUM | 8 | 3 |
| Laura Sánchez | +34600000002 | ASYLUM | 10 | 2 |
| Carmen Díaz | +34600000003 | ARRAIGO | 6 | 4 |
| José Martínez | +34600000004 | ARRAIGO | 12 | 3 |
| Elena Ruiz | +34600000005 | STUDENT | 7 | 2 |
| Antonio López | +34600000006 | STUDENT | 9 | 5 |
| Rosa Fernández | +34600000007 | IRREGULAR | 6 | 2 |
| Pedro González | +34600000008 | IRREGULAR | 11 | 3 |
| Isabel Moreno | +34600000009 | OTHER | 6 | 1 |
| Francisco Jiménez | +34600000010 | OTHER | 8 | 2 |

Each client has:
- **6-12 conversations** with realistic Spanish immigration keywords
- **1-5 PDF documents** stored locally
- Automatic profile classification based on message content

### Mock Users (5 total)

| Name | Email | Role | Use Case |
|------|-------|------|----------|
| Admin User | admin@mock.local | admin | Full system access |
| María García | lawyer1@mock.local | lawyer | Primary lawyer |
| Carlos Rodríguez | lawyer2@mock.local | lawyer | Secondary lawyer |
| Ana López | assistant1@mock.local | assistant | Administrative support |
| Guest Viewer | viewer@mock.local | viewer | Read-only access |

### Storage Structure

Mock files are stored at:
```
backend/
  .local_storage/
    mock.db                    # SQLite database
    files/                     # Document storage
      ASYLUM/
        Miguel_Hernandez_<uuid>/
          document_1.pdf
          passport.pdf
      ARRAIGO/
        Carmen_Diaz_<uuid>/
          ...
```

Files are accessible via:
- Direct download: `GET /mock-storage/{path}`
- Signed URL: `GET /documents/{document_id}/signed-url` (redirects to mock-storage)

---

## Environment Variables

### Backend (.env)

```bash
# Core Configuration
APP_MODE=mock                    # 'mock' or 'real'
MOCK_SEED_ON_START=true         # Auto-seed on startup
STORAGE_MODE=local              # 'local' or 'supabase'
DB_MODE=sqlite                  # 'sqlite', 'postgres', or 'supabase'

# WhatsApp (not needed in mock mode but can set dummy values)
WHATSAPP_PHONE_NUMBER_ID=mock
WHATSAPP_ACCESS_TOKEN=mock
WHATSAPP_VERIFY_TOKEN=mock123

# Supabase (not needed in mock mode)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### Frontend (.env)

```bash
# Mode
VITE_APP_MODE=mock              # 'mock' or 'real'

# API
VITE_API_BASE_URL=http://localhost:8000

# Supabase (not needed in mock mode)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

---

## API Endpoints

### Standard Endpoints (work in both modes)

```bash
# Clients
GET  /clients                   # List all clients
GET  /clients/{id}              # Get client details
GET  /clients/{id}/conversations
GET  /clients/{id}/documents

# Documents
GET  /documents/{id}/signed-url

# Health
GET  /health
```

### Mock-Only Endpoints

```bash
# File access
GET  /mock-storage/{path}       # Direct file download

# Mock authentication
POST /mock-auth/login
  Body: { "email": "admin@mock.local" }
  Returns: { "user": {...}, "token": "..." }

GET  /mock-auth/session         # Get current session
POST /mock-auth/logout          # Sign out
GET  /mock-auth/users           # List all mock users
```

---

## Testing Workflows

### 1. Test Client Management

```bash
# List clients
curl http://localhost:8000/clients

# Get specific client
curl http://localhost:8000/clients/{client_id}
```

### 2. Test Conversations

```bash
# Get client conversations
curl http://localhost:8000/clients/{client_id}/conversations
```

### 3. Test Document Storage

```bash
# List documents
curl http://localhost:8000/clients/{client_id}/documents

# Download document (get signed URL then download)
curl http://localhost:8000/documents/{document_id}/signed-url
```

### 4. Test Profile Classification

Messages are automatically classified based on keywords:

- **ASYLUM**: `"asilo", "refugiado", "persecución"`
- **ARRAIGO**: `"arraigo", "vinculación", "residencia"`
- **STUDENT**: `"estudiante", "universidad", "curso"`
- **IRREGULAR**: `"indocumentado", "sin papeles"`
- **OTHER**: Default fallback

Check client profile updates after viewing conversations.

---

## Resetting Mock Data

### Option 1: Restart Backend (if MOCK_SEED_ON_START=true)

```bash
# Delete existing data
rm -rf backend/.local_storage

# Restart backend (will auto-seed)
uvicorn app.main:app --reload
```

### Option 2: Manual Seed

```python
# In Python shell or script
from app.adapters.mock.seed import seed_mock_data
from app.adapters.mock.mock_repository import MockRepository
from app.adapters.mock.mock_storage import MockStorage

repo = MockRepository()
storage = MockStorage()
seed_mock_data(repo, storage)
```

---

## Syncing to Production

When ready to move mock data to Supabase:

```bash
# 1. Configure Supabase credentials in .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key

# 2. Run sync script
cd backend
python -m app.scripts.sync_to_supabase
```

This will:
1. Create all clients in Supabase (mapping mock UUIDs to real UUIDs)
2. Create all conversations linked to real clients
3. Upload all files to Supabase Storage
4. Create document records with correct storage paths

**Note**: Script is idempotent - you can run it multiple times and it will skip existing records.

---

## Switching to Production Mode

After syncing, switch to production:

### Backend
```bash
# .env
APP_MODE=real
STORAGE_MODE=supabase
DB_MODE=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key

# WhatsApp
WHATSAPP_PHONE_NUMBER_ID=your-real-id
WHATSAPP_ACCESS_TOKEN=your-real-token
WHATSAPP_VERIFY_TOKEN=your-verify-token
```

### Frontend
```bash
# .env
VITE_APP_MODE=real
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

Restart both backend and frontend. Application will now use real Supabase and WhatsApp.

---

## Architecture

### Adapter Pattern

All services use abstract interfaces:

```
app/adapters/
  ├── repository_base.py      # Database interface
  ├── storage_base.py         # File storage interface
  ├── whatsapp_base.py        # WhatsApp client interface
  ├── factory.py              # Dependency injection
  ├── mock/                   # Mock implementations
  │   ├── mock_repository.py  # SQLite
  │   ├── mock_storage.py     # Local filesystem
  │   └── mock_whatsapp.py    # Fixture-based
  └── real/                   # Production implementations
      ├── supabase_repository.py
      ├── supabase_storage.py
      └── meta_whatsapp.py
```

Factory pattern (`factory.py`) provides correct implementation based on `APP_MODE`.

### Mock Storage

- **Database**: SQLite at `backend/.local_storage/mock.db`
- **Files**: Local filesystem at `backend/.local_storage/files/`
- **WhatsApp PDFs**: Fixtures at `backend/app/fixtures/pdfs/`

### Frontend Auth

- **Mock Mode**: Uses `localStorage` with base64-encoded tokens
- **Real Mode**: Uses Supabase Auth with JWT
- Both protected by `ProtectedRoute.tsx`

---

## Troubleshooting

### Backend won't start

```bash
# Check Python version (need 3.10+)
python --version

# Reinstall dependencies
pip install -r requirements.txt

# Check .env is configured
cat .env | grep APP_MODE
```

### Mock data not seeding

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Manually trigger seed
python -c "from app.adapters.mock.seed import seed_mock_data; from app.adapters.mock.mock_repository import MockRepository; from app.adapters.mock.mock_storage import MockStorage; seed_mock_data(MockRepository(), MockStorage())"
```

### Can't login in frontend

- Verify `VITE_APP_MODE=mock` in `frontend/.env`
- Check browser console for errors
- Try clearing localStorage: `localStorage.clear()`

### Documents not downloading

```bash
# Check files exist
ls -la backend/.local_storage/files/

# Test mock-storage endpoint
curl http://localhost:8000/mock-storage/ASYLUM/Miguel_Hernandez_{uuid}/document_1.pdf
```

### Sync to Supabase fails

- Verify Supabase credentials are correct
- Check Supabase Storage bucket exists and is accessible
- Check Supabase database tables match schema
- Run sync with verbose logging: `LOG_LEVEL=DEBUG python -m app.scripts.sync_to_supabase`

---

## Development Tips

### Add More Mock Clients

Edit `backend/app/adapters/mock/seed.py`:

```python
MOCK_CLIENTS = [
    # ... existing clients ...
    {
        "name": "New Client",
        "phone": "+34600000011",
        "profile": "ASYLUM",
    },
]
```

### Customize Mock Messages

Edit conversation generation in `seed.py`:

```python
MESSAGE_TEMPLATES = {
    "ASYLUM": [
        "Need help with asylum application",
        "When is my interview?",
        # Add more...
    ],
}
```

### Mock User Permissions

Extend `frontend/src/lib/mockAuth.ts`:

```typescript
export const MOCK_USERS: MockUser[] = [
  { 
    id: '6', 
    email: 'newuser@mock.local', 
    name: 'New User', 
    role: 'custom_role' 
  },
]
```

---

## Production Checklist

Before deploying to production:

- [ ] Switch `APP_MODE=real` in backend `.env`
- [ ] Switch `VITE_APP_MODE=real` in frontend `.env`
- [ ] Configure real Supabase credentials
- [ ] Configure real WhatsApp Business API credentials
- [ ] Run sync script if migrating mock data
- [ ] Test authentication with real Supabase users
- [ ] Test WhatsApp webhook with Meta's test tool
- [ ] Remove or secure mock endpoints in production
- [ ] Update CORS settings for production domain

---

## Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Supabase Docs**: https://supabase.com/docs
- **WhatsApp Business API**: https://developers.facebook.com/docs/whatsapp
- **Vite Environment Variables**: https://vitejs.dev/guide/env-and-mode.html
