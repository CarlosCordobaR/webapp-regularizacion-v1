# TODO Backlog - WhatsApp Regularization MVP

**Last Updated**: 2025-02-11  
**Status**: 7 P0 items blocking production launch

---

## Priority Legend
- **P0 (🔴)**: Production blocker - Must fix before go-live
- **P1 (🟠)**: Critical - Fix within 2 weeks of launch
- **P2 (🟡)**: Important - Fix within 1 month of launch
- **P3 (🔵)**: Nice-to-have - Roadmap item

---

## P0 Tasks (Production Blockers)

### 🔴 P0-1: Enable Row Level Security (RLS)
**Component**: Backend Database  
**Files**: 
- [backend/app/db/schema.sql](../backend/app/db/schema.sql#L125-L169)

**Current State**: RLS policies defined but commented out. Any authenticated user can access all data.

**Acceptance Criteria**:
- [ ] Uncomment `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` lines (L130-L132)
- [ ] Uncomment policy definitions (L136-L169)
- [ ] Test with non-admin Supabase user: should see 0 clients
- [ ] Test with service role key: should see all clients
- [ ] Document RLS bypass for backend service role in README

**Steps**:
```bash
# 1. Edit schema.sql - uncomment RLS blocks
# 2. Apply to Supabase
psql $DATABASE_URL -f backend/app/db/schema.sql

# 3. Create test user in Supabase dashboard
# 4. Test with curl using user JWT
curl -H "Authorization: Bearer $USER_JWT" http://localhost:8000/clients
# Expected: []

# 5. Test with service role
curl -H "Authorization: Bearer $SERVICE_ROLE_KEY" http://localhost:8000/clients
# Expected: [...clients...]
```

**Risks**: If mistakenly applied to service role connection, backend will break.

**Estimated Effort**: 2 hours

---

### 🔴 P0-2: Add Webhook Signature Verification
**Component**: Backend WhatsApp  
**Files**: 
- [backend/app/whatsapp/webhook.py](../backend/app/whatsapp/webhook.py#L18)

**Current State**: POST /webhook accepts any JSON payload. No signature validation.

**Acceptance Criteria**:
- [ ] Read `X-Hub-Signature-256` header in POST handler
- [ ] Compute HMAC-SHA256 of raw body using `WHATSAPP_APP_SECRET`
- [ ] Compare with provided signature (constant-time comparison)
- [ ] Return 401 if signatures don't match
- [ ] Log failed verification attempts
- [ ] Add test case with valid/invalid signatures

**Steps**:
```python
# Add to webhook.py WebhookHandler class
import hmac
import hashlib
from fastapi import Request, HTTPException

async def verify_signature(self, request: Request, body: bytes) -> bool:
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    expected = hmac.new(
        self.app_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(f"sha256={expected}", signature):
        logger.warning(f"Invalid webhook signature from {request.client.host}")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True

# Update POST webhook handler
@router.post("/webhook")
async def webhook_handler(request: Request):
    body = await request.body()
    await handler.verify_signature(request, body)
    data = json.loads(body)
    # ... rest of handler
```

**Risks**: WhatsApp will retry failed webhooks. Test thoroughly in mock mode first.

**Estimated Effort**: 3 hours

---

### 🔴 P0-3: Add Backend Authentication Middleware
**Component**: Backend API  
**Files**: 
- NEW: `backend/app/core/auth.py`
- [backend/app/main.py](../backend/app/main.py) (register dependency)

**Current State**: No JWT validation. Any request accepted.

**Acceptance Criteria**:
- [ ] Create `verify_jwt()` dependency in core/auth.py
- [ ] Validate Supabase JWT signature using SUPABASE_JWT_SECRET
- [ ] Check token expiration
- [ ] Extract user ID from token
- [ ] Exclude /webhook, /health, /mock-auth from validation
- [ ] Return 401 for invalid/expired tokens
- [ ] Add test with valid/invalid/expired JWTs

**Steps**:
```python
# backend/app/core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()

async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Verify Supabase JWT and return user ID."""
    if settings.app_mode == "mock":
        return "mock-user-id"  # Bypass in mock mode
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated"
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# In each API router, add dependency
@router.get("/clients")
async def list_clients(
    user_id: str = Depends(verify_jwt),  # <-- Add this
    page: int = 1,
    limit: int = 50
):
    # ... existing code
```

**Risks**: Will break frontend if tokens not properly sent. Test mock mode separately.

**Estimated Effort**: 4 hours

---

### 🔴 P0-4: Create .env Files from Templates
**Component**: Configuration  
**Files**: 
- NEW: `backend/.env`
- NEW: `frontend/.env`
- Templates: [backend/.env.example](../backend/.env.example), [frontend/.env.example](../frontend/.env.example)

**Current State**: .env files must be created manually. Fresh clone won't start.

**Acceptance Criteria**:
- [ ] Copy .env.example to .env in both directories
- [ ] Replace all `your_*` placeholders with real values
- [ ] Validate backend starts: `cd backend && uvicorn app.main:app`
- [ ] Validate frontend starts: `cd frontend && npm run dev`
- [ ] Add `.env` to .gitignore if not already present
- [ ] Update README with "Step 0: Configure .env files"

**Steps**:
```bash
# Backend
cd backend
cp .env.example .env
# Edit .env:
# - SUPABASE_URL=https://your-project.supabase.co
# - SUPABASE_SERVICE_ROLE_KEY=eyJ...
# - DATABASE_URL=postgresql://postgres:[password]@...
# - WHATSAPP_API_TOKEN=EAAc...

# Frontend
cd ../frontend
cp .env.example .env
# Edit .env:
# - VITE_SUPABASE_URL=https://your-project.supabase.co
# - VITE_SUPABASE_ANON_KEY=eyJ...
# - VITE_API_URL=http://localhost:8000

# Test
cd ../backend && uvicorn app.main:app --reload &
cd ../frontend && npm run dev
```

**Risks**: Committing .env with secrets to git. Double-check .gitignore.

**Estimated Effort**: 1 hour

---

### 🔴 P0-5: Configure Storage Bucket Permissions
**Component**: Backend Storage  
**Files**: 
- Supabase dashboard → Storage → documents bucket

**Current State**: Bucket permissions unknown. Documents may be public/inaccessible.

**Acceptance Criteria**:
- [ ] Set bucket to **private** (not public)
- [ ] Verify RLS policies exist: only service role can read/write
- [ ] Test document upload: should succeed with service role key
- [ ] Test document download: should return presigned URL (60s expiry)
- [ ] Test unauthenticated access: should fail with 403
- [ ] Document bucket policy in README

**Steps**:
1. Go to Supabase Dashboard → Storage → `documents` bucket
2. Settings → **Public**: OFF
3. Policies → Add policy:
   ```sql
   CREATE POLICY "Service role can read documents"
   ON storage.objects FOR SELECT
   TO service_role
   USING (bucket_id = 'documents');

   CREATE POLICY "Service role can insert documents"
   ON storage.objects FOR INSERT
   TO service_role
   WITH CHECK (bucket_id = 'documents');
   ```
4. Test with Postman:
   - Upload: `POST /documents` with service role JWT → 200
   - Download: `GET /documents/{id}/download` → presigned URL
   - Direct access to URL without auth → 403

**Risks**: Misconfigured policy could expose all documents publicly.

**Estimated Effort**: 2 hours

---

### 🔴 P0-6: Add Email Uniqueness Constraint
**Component**: Backend Database  
**Files**: 
- [backend/app/db/schema.sql](../backend/app/db/schema.sql#L18)
- [backend/prisma/schema.prisma](../backend/prisma/schema.prisma#L18)

**Current State**: Email field exists but allows duplicates.

**Acceptance Criteria**:
- [ ] Add `UNIQUE` constraint to `clients.email` column
- [ ] Handle NULL emails (allow multiple NULLs or enforce NOT NULL?)
- [ ] Update Prisma schema: `email String? @unique`
- [ ] Update API error handling: return 409 on duplicate email
- [ ] Add test: create two clients with same email → second fails
- [ ] Document constraint in README

**Steps**:
```sql
-- Option 1: Allow multiple NULLs (partial unique index)
CREATE UNIQUE INDEX unique_client_email 
ON clients(email) 
WHERE email IS NOT NULL;

-- Option 2: Enforce email required (may break existing data)
ALTER TABLE clients 
ALTER COLUMN email SET NOT NULL;

ALTER TABLE clients 
ADD CONSTRAINT unique_client_email UNIQUE (email);
```

```python
# Update backend/app/api/clients.py
from psycopg2.errors import UniqueViolation

@router.post("/clients")
async def create_client(...):
    try:
        client = repository.create_client(client_data)
        return client
    except UniqueViolation:
        raise HTTPException(status_code=409, detail="Email already registered")
```

**Risks**: Existing duplicate emails will cause migration failure. Clean data first.

**Estimated Effort**: 2 hours

---

### 🔴 P0-7: Set Up CI/CD Pipeline
**Component**: DevOps  
**Files**: 
- NEW: `.github/workflows/ci.yml`
- NEW: `.github/workflows/deploy.yml`

**Current State**: No automated testing or deployment.

**Acceptance Criteria**:
- [ ] CI workflow runs on every PR: linting + tests
- [ ] Fail PR if tests fail or coverage < 70%
- [ ] Deploy workflow triggers on merge to `main`
- [ ] Deploy backend to Azure App Service / Railway / Render
- [ ] Deploy frontend to Vercel / Netlify
- [ ] Set environment secrets in GitHub repo settings
- [ ] Add status badge to README

**Steps**:
```yaml
# .github/workflows/ci.yml
name: CI
on: [pull_request]
jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: cd backend && pip install -r requirements.txt
      - run: cd backend && pytest --cov=app --cov-report=term-missing
      - run: |
          COVERAGE=$(pytest --cov=app --cov-report=json | jq .totals.percent_covered)
          if (( $(echo "$COVERAGE < 70" | bc -l) )); then
            echo "Coverage $COVERAGE% is below 70%"
            exit 1
          fi
  
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run lint
      - run: cd frontend && npm run build

# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      # ... deploy to chosen platform
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      # ... deploy to Vercel/Netlify
```

**Risks**: Deploy failures can take down production. Use staging environment first.

**Estimated Effort**: 6 hours

---

## P1 Tasks (Critical - Fix Within 2 Weeks)

### 🟠 P1-1: Add API Rate Limiting
**Component**: Backend API  
**Estimated Effort**: 2 hours  
**Files**: `backend/app/main.py`

**Steps**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# On webhook endpoint
@router.post("/webhook")
@limiter.limit("10/minute")  # More restrictive
async def webhook_handler():
    ...
```

---

### 🟠 P1-2: Add Document Deletion Endpoint
**Component**: Backend API  
**Estimated Effort**: 2 hours  
**Files**: [backend/app/api/documents.py](../backend/app/api/documents.py)

**Steps**:
```python
@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    user_id: str = Depends(verify_jwt),
    repository: RepositoryBase = Depends(get_repository),
    storage: StorageBase = Depends(get_storage)
) -> Dict[str, str]:
    # 1. Get document to verify ownership
    doc = repository.get_document(UUID(document_id))
    if not doc:
        raise HTTPException(404, "Document not found")
    
    # 2. Delete from storage
    storage.delete_file(doc["storage_path"])
    
    # 3. Delete from database
    repository.delete_document(UUID(document_id))
    
    return {"message": "Document deleted"}
```

---

### 🟠 P1-3: Implement Real WhatsApp Send Message
**Component**: Backend WhatsApp  
**Estimated Effort**: 4 hours  
**Files**: NEW `backend/app/adapters/real/whatsapp.py`

**Steps**:
```python
# backend/app/adapters/real/whatsapp.py
import httpx
from app.core.config import get_settings

class RealWhatsAppAdapter:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = f"https://graph.facebook.com/v18.0/{self.settings.whatsapp_phone_number_id}"
    
    async def send_message(self, to: str, body: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "Authorization": f"Bearer {self.settings.whatsapp_api_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {"body": body}
                }
            )
            response.raise_for_status()
            return response.json()
```

---

### 🟠 P1-4: Add Migration System (Alembic)
**Component**: Backend Database  
**Estimated Effort**: 4 hours  
**Files**: NEW `backend/alembic.ini`, `backend/alembic/`

**Steps**:
```bash
cd backend
pip install alembic
alembic init alembic
# Edit alembic.ini - set sqlalchemy.url
# Edit alembic/env.py - import models

# Create first migration
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

### 🟠 P1-5: Add Client Deletion Endpoint
**Component**: Backend API  
**Estimated Effort**: 2 hours  
**Files**: [backend/app/api/clients.py](../backend/app/api/clients.py)

**Acceptance Criteria**:
- [ ] Add `DELETE /clients/{client_id}` endpoint
- [ ] Soft delete: set status to 'archived'
- [ ] Hard delete option: actually remove from DB (cascade to conversations/documents)
- [ ] Require confirmation parameter: `?confirm=true`

---

## P2 Tasks (Important - Fix Within 1 Month)

### 🟡 P2-1: Add Conversation Timeline UI Component
**Component**: Frontend  
**Estimated Effort**: 6 hours  
**Files**: NEW `frontend/src/components/ConversationTimeline.tsx`

**Description**: Display message history on ClientDetail page. Show inbound/outbound messages with timestamps and media attachments.

---

### 🟡 P2-2: Enable FastAPI Auto-Documentation
**Component**: Backend API  
**Estimated Effort**: 1 hour  
**Files**: [backend/app/main.py](../backend/app/main.py)

**Steps**:
```python
# main.py - add to app init
app = FastAPI(
    title="WhatsApp Regularization API",
    description="Manage immigration clients via WhatsApp",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```
Access at http://localhost:8000/docs

---

### 🟡 P2-3: Add Confidence Scoring to Classifier
**Component**: Backend Services  
**Estimated Effort**: 4 hours  
**Files**: [backend/app/services/classifier.py](../backend/app/services/classifier.py)

**Steps**:
- Return `{profile_type: "ASYLUM", confidence: 0.85}` instead of just type
- Multi-keyword matches = higher confidence
- Update API response to include confidence field

---

### 🟡 P2-4: Add Frontend Unit Tests
**Component**: Frontend  
**Estimated Effort**: 8 hours  
**Files**: NEW `frontend/src/components/__tests__/`

**Description**: Add Vitest + React Testing Library tests for CreateClientModal, EditClientModal, ClientDetail.

---

### 🟡 P2-5: Add Structured Logging
**Component**: Backend Observability  
**Estimated Effort**: 3 hours  
**Files**: [backend/app/core/logging.py](../backend/app/core/logging.py)

**Steps**:
- Replace print statements with `logger.info()` calls
- Add request ID to all logs for tracing
- Log all webhook events with client_id for debugging

---

### 🟡 P2-6: Add Error Tracking (Sentry)
**Component**: Backend/Frontend  
**Estimated Effort**: 2 hours  
**Files**: `backend/app/main.py`, `frontend/src/main.tsx`

**Steps**:
```python
# backend
import sentry_sdk
sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
```

```typescript
// frontend
import * as Sentry from "@sentry/react";
Sentry.init({ dsn: import.meta.env.VITE_SENTRY_DSN });
```

---

### 🟡 P2-7: Add Load Testing
**Component**: Testing  
**Estimated Effort**: 4 hours  
**Files**: NEW `backend/load_tests/webhook_burst.py`

**Description**: Use Locust to simulate 100 concurrent webhook POSTs. Ensure no messages lost or duplicated.

---

## P3 Tasks (Nice-to-Have - Roadmap)

### 🔵 P3-1: Add Audit Logging for GDPR Compliance
- Track all data access (who viewed which client when)
- Add `GET /clients/{id}/audit-log` endpoint
- Store in separate `audit_logs` table

### 🔵 P3-2: Add Bulk Client Import (CSV Upload)
- Upload CSV with columns: phone, name, email, profileType
- Validate all rows before inserting
- Return summary report

### 🔵 P3-3: Add Client Search/Filter
- Frontend: search by name, phone, email
- Backend: add query params to `GET /clients?search=...`

### 🔵 P3-4: Add WhatsApp Template Message Support
- Send structured message templates (buttons, lists)
- Store template definitions in database

### 🔵 P3-5: Add Dashboard/Analytics Page
- Total clients by profile type (pie chart)
- Messages per day (line chart)
- Document upload status (bar chart)

---

## Summary

| Priority | Count | Total Effort |
|----------|-------|--------------|
| P0 🔴    | 7     | 20 hours (~3 days) |
| P1 🟠    | 5     | 14 hours (~2 days) |
| P2 🟡    | 7     | 28 hours (~4 days) |
| P3 🔵    | 5     | TBD (roadmap) |

**Critical Path to Launch**: P0 items must be completed. Estimated **1 week** (1 engineer).

**Recommended Sprint 1**: P0-1 through P0-7 (production blockers)  
**Recommended Sprint 2**: P1-1 through P1-5 (critical improvements)  
**Recommended Sprint 3**: P2 items based on user feedback

---

**Last Updated**: 2025-02-11  
**Next Review**: After P0 sprint completion
