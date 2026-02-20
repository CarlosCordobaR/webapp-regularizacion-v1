# Quick Start Guide

This guide will help you get the WhatsApp Business webhook MVP running locally in minutes.

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Supabase project created
- [ ] WhatsApp Business API credentials obtained

## Step-by-Step Setup

### 1. Supabase Setup (5 minutes)

1. Go to https://supabase.com and create a new project
2. Once created, go to **Project Settings → API**:
   - Copy your Project URL
   - Copy your `anon` public key
   - Copy your `service_role` secret key

3. Go to **SQL Editor** and run the schema:
   ```bash
   # Copy the contents of backend/app/db/schema.sql
   # Paste into SQL Editor and click "Run"
   ```

4. Go to **Storage** and create a bucket:
   - Name: `client-documents`
   - Public bucket: ✓ Yes (for MVP simplicity)

5. Go to **Authentication → Users**:
   - Click "Add user" → "Create new user"
   - Email: your-email@example.com
   - Password: your-secure-password
   - Email confirm: ✓ (or manually verify)

### 2. Backend Setup (5 minutes)

```bash
cd mvp_whatsapp_files/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Create .env file
cp ../.env.example .env

# Edit .env with your credentials (use nano, vim, or any editor)
nano .env
```

**Fill in these values in `.env`:**
```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...
STORAGE_BUCKET=client-documents

WHATSAPP_TOKEN=EAAxxxxx  # Your WhatsApp token
WHATSAPP_PHONE_NUMBER_ID=123456789
WHATSAPP_BUSINESS_ACCOUNT_ID=123456789
VERIFY_TOKEN=my_secret_verify_token_123  # Choose any secret string

APP_BASE_URL=http://localhost:8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

**Test the backend:**
```bash
# Run tests
python -m pytest app/tests/ -v

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, test health endpoint
curl http://localhost:8000/health
# Should return: {"status":"ok","service":"whatsapp-webhook-api"}
```

### 3. Frontend Setup (3 minutes)

```bash
cd mvp_whatsapp_files/frontend

# Install dependencies
npm install

# Create .env.local (optional, for custom config)
cat > .env.local << EOF
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJxxx...
VITE_API_BASE_URL=http://localhost:8000
EOF

# Start dev server
npm run dev
```

Frontend will be available at **http://localhost:5173**

### 4. Test the Application (2 minutes)

1. Open http://localhost:5173 in your browser
2. Login with the email/password you created in Supabase
3. You should see an empty clients list (normal for fresh install)

### 5. Setup Webhook for Local Testing (5 minutes)

**Install ngrok:**
```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

**Expose your local backend:**
```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding   https://abc123.ngrok.io -> http://localhost:8000
```

**Configure WhatsApp webhook:**

1. Go to your Meta App Dashboard: https://developers.facebook.com/apps/
2. Navigate to WhatsApp → Configuration
3. In "Webhook" section, click "Edit"
4. Enter:
   - **Callback URL**: `https://abc123.ngrok.io/webhook`
   - **Verify token**: (the VERIFY_TOKEN from your .env)
5. Click "Verify and Save"
6. Subscribe to webhook fields: `messages`

### 6. Test Webhook (2 minutes)

**Test verification endpoint:**
```bash
curl "http://localhost:8000/webhook?hub.mode=subscribe&hub.verify_token=my_secret_verify_token_123&hub.challenge=test123"
# Should return: test123
```

**Test webhook POST with sample message:**
```bash
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
            "profile": {"name": "Test User"},
            "wa_id": "1234567890"
          }],
          "messages": [{
            "from": "1234567890",
            "id": "wamid.test123",
            "timestamp": "1234567890",
            "text": {"body": "Necesito ayuda con mi proceso de asilo"},
            "type": "text"
          }]
        },
        "field": "messages"
      }]
    }]
  }'
```

**Check the results:**
1. Refresh the frontend (http://localhost:5173/clients)
2. You should see a new client "Test User" with phone "1234567890"
3. Profile type should be "ASYLUM" (keyword detected)
4. Click on the client to see the conversation

### 7. Send Real WhatsApp Message (Optional)

If you have WhatsApp Business API test number set up:

1. Send a WhatsApp message to your test number
2. Message should appear in your local app within seconds
3. Check the backend logs to see processing

## Common Issues

**Backend won't start:**
- Check `.env` file exists and has all required values
- Verify Supabase credentials are correct
- Ensure virtual environment is activated

**Frontend login fails:**
- Verify Supabase user exists and is confirmed
- Check browser console for errors
- Verify VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY

**Webhook not receiving messages:**
- Ensure ngrok is running
- Verify webhook URL in Meta Dashboard is correct
- Check VERIFY_TOKEN matches
- Look at backend logs for errors

## Next Steps

1. **Send test messages** with different keywords:
   - "asilo" → ASYLUM
   - "arraigo" → ARRAIGO
   - "estudiante" → STUDENT
   - "irregular" → IRREGULAR

2. **Send a document/PDF** via WhatsApp:
   - Should be stored in Supabase Storage
   - Will appear in Documents tab for the client

3. **Review storage**:
   - Go to Supabase Storage → client-documents
   - Check files are organized by profile type

## Production Deployment

When ready for production, see the main README.md for deployment instructions to:
- Railway / Render / Fly.io (backend)
- Vercel / Netlify (frontend)
- Enable RLS policies in Supabase
- Use production WhatsApp webhook URL

## Support

If you encounter issues:
1. Check backend logs: `tail -f backend/logs/app.log` (if logging to file)
2. Check browser console for frontend errors
3. Verify all environment variables are set correctly
4. Test each component individually (backend health, frontend login, webhook)
