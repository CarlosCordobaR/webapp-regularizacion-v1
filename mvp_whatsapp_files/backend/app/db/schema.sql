-- WhatsApp Business Cloud API → Supabase MVP
-- Database Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enums
CREATE TYPE profile_type AS ENUM (
    'ASYLUM',
    'ARRAIGO',
    'STUDENT',
    'IRREGULAR',
    'OTHER'
);

CREATE TYPE message_direction AS ENUM (
    'INBOUND',
    'OUTBOUND',
    'inbound',
    'outbound'
);

CREATE TYPE client_status AS ENUM (
    'active',
    'inactive',
    'archived'
);

CREATE TYPE document_type AS ENUM (
    'TASA',
    'PASSPORT_NIE'
);

-- Clients table
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    passport_or_nie TEXT NOT NULL,
    profile_type profile_type DEFAULT 'OTHER',
    status client_status DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    direction message_direction NOT NULL,
    content TEXT,
    message_type VARCHAR(50) NOT NULL,
    dedupe_key VARCHAR(64) UNIQUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON COLUMN conversations.dedupe_key IS 'SHA256 hash for idempotent sync: sha256(client_id|direction|created_at|type|content)';

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    storage_path TEXT NOT NULL UNIQUE,
    original_filename VARCHAR(255),
    mime_type VARCHAR(100),
    file_size BIGINT,
    profile_type profile_type,
    document_type document_type,
    metadata JSONB DEFAULT '{}',
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_client_document_type UNIQUE (client_id, document_type)
);

COMMENT ON COLUMN documents.storage_path IS 'Unique storage path in Supabase Storage for idempotent sync';

-- Document versions table (version history for typed documents)
CREATE TABLE document_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    document_type document_type NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    version_number INTEGER NOT NULL,
    content_sha256 VARCHAR(64) NOT NULL,
    storage_path TEXT NOT NULL,
    original_filename VARCHAR(255),
    mime_type VARCHAR(100),
    file_size BIGINT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_client_doc_type_version UNIQUE (client_id, document_type, version_number),
    CONSTRAINT unique_client_doc_type_sha UNIQUE (client_id, document_type, content_sha256)
);

-- Audit events table (operational traceability)
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(64),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Export jobs table (tracks generated ZIP exports and expiration)
CREATE TABLE export_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL UNIQUE,
    status VARCHAR(32) NOT NULL DEFAULT 'ready',
    accepted_only BOOLEAN NOT NULL DEFAULT TRUE,
    file_size BIGINT,
    expires_at TIMESTAMPTZ NOT NULL,
    requested_by VARCHAR(128),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sync mappings table (tracks mock UUID -> Supabase UUID for reference)
CREATE TABLE sync_mappings (
    mock_id UUID NOT NULL,
    supabase_id UUID NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    synced_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (mock_id, entity_type)
);

CREATE INDEX idx_sync_mappings_entity_type ON sync_mappings(entity_type);

COMMENT ON TABLE sync_mappings IS 'Tracks mapping between mock dataset UUIDs and Supabase UUIDs';

-- Indexes for performance
CREATE INDEX idx_clients_phone ON clients(phone_number);
CREATE INDEX idx_clients_profile_type ON clients(profile_type);
CREATE INDEX idx_clients_status ON clients(status);
CREATE INDEX idx_clients_created_at ON clients(created_at DESC);

CREATE INDEX idx_conversations_client_id ON conversations(client_id);
CREATE INDEX idx_conversations_client_created ON conversations(client_id, created_at DESC);
CREATE INDEX idx_conversations_message_id ON conversations(message_id);
CREATE INDEX idx_conversations_direction ON conversations(direction);
CREATE INDEX idx_conversations_dedupe_key ON conversations(dedupe_key);

CREATE INDEX idx_documents_client_id ON documents(client_id);
CREATE INDEX idx_documents_client_uploaded ON documents(client_id, uploaded_at DESC);
CREATE INDEX idx_documents_conversation_id ON documents(conversation_id);
CREATE INDEX idx_documents_profile_type ON documents(profile_type);
CREATE INDEX idx_document_versions_client_type_created ON document_versions(client_id, document_type, created_at DESC);
CREATE INDEX idx_document_versions_sha ON document_versions(content_sha256);
CREATE INDEX idx_audit_events_client_created ON audit_events(client_id, created_at DESC);
CREATE INDEX idx_export_jobs_client_created ON export_jobs(client_id, created_at DESC);
CREATE INDEX idx_export_jobs_expires_at ON export_jobs(expires_at);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for clients table
CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) - MVP Configuration
-- For MVP: Simple policies for authenticated users
-- Disable RLS for initial setup, enable once ready for production

-- Enable RLS
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE export_jobs ENABLE ROW LEVEL SECURITY;

-- Policies for authenticated users (internal staff)
-- Allow authenticated users to read all data
CREATE POLICY "Allow authenticated read access on clients"
    ON clients FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read access on conversations"
    ON conversations FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read access on documents"
    ON documents FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read access on document_versions"
    ON document_versions FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read access on audit_events"
    ON audit_events FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow authenticated read access on export_jobs"
    ON export_jobs FOR SELECT
    TO authenticated
    USING (true);

-- Service role has full access (for backend operations)
CREATE POLICY "Allow service role full access on clients"
    ON clients FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access on conversations"
    ON conversations FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access on documents"
    ON documents FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access on document_versions"
    ON document_versions FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access on audit_events"
    ON audit_events FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Allow service role full access on export_jobs"
    ON export_jobs FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Storage bucket setup
-- Run this in Supabase dashboard Storage section or via API:
-- 1. Create bucket named "client-documents"
-- 2. Set as public for MVP (or private with signed URLs)
-- 3. Optional: Set file size limits and allowed MIME types

-- Sample data for testing (optional)
-- INSERT INTO clients (phone_number, name, profile_type, status)
-- VALUES 
--     ('1234567890', 'John Doe', 'ASYLUM', 'active'),
--     ('0987654321', 'Jane Smith', 'STUDENT', 'active');

-- Useful queries for monitoring
-- SELECT profile_type, COUNT(*) FROM clients GROUP BY profile_type;
-- SELECT client_id, COUNT(*) as message_count FROM conversations GROUP BY client_id ORDER BY message_count DESC LIMIT 10;
-- SELECT client_id, COUNT(*) as doc_count FROM documents GROUP BY client_id ORDER BY doc_count DESC LIMIT 10;
