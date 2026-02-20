-- Migration: Add document versioning and audit trail tables
-- Description: Implements RM26-042 (versioning + SHA256 dedupe + DOC_UPLOADED audit)

CREATE TABLE IF NOT EXISTS document_versions (
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

CREATE TABLE IF NOT EXISTS audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(64),
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_versions_client_type_created
    ON document_versions(client_id, document_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_document_versions_sha
    ON document_versions(content_sha256);

CREATE INDEX IF NOT EXISTS idx_audit_events_client_created
    ON audit_events(client_id, created_at DESC);

ALTER TABLE document_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'document_versions'
          AND policyname = 'Allow authenticated read access on document_versions'
    ) THEN
        CREATE POLICY "Allow authenticated read access on document_versions"
            ON document_versions FOR SELECT
            TO authenticated
            USING (true);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'audit_events'
          AND policyname = 'Allow authenticated read access on audit_events'
    ) THEN
        CREATE POLICY "Allow authenticated read access on audit_events"
            ON audit_events FOR SELECT
            TO authenticated
            USING (true);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'document_versions'
          AND policyname = 'Allow service role full access on document_versions'
    ) THEN
        CREATE POLICY "Allow service role full access on document_versions"
            ON document_versions FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'audit_events'
          AND policyname = 'Allow service role full access on audit_events'
    ) THEN
        CREATE POLICY "Allow service role full access on audit_events"
            ON audit_events FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END
$$;
