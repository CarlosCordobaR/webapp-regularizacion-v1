-- RM26-070: Export jobs registry for accepted-only expediente ZIPs

CREATE TABLE IF NOT EXISTS export_jobs (
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

CREATE INDEX IF NOT EXISTS idx_export_jobs_client_created
    ON export_jobs(client_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_export_jobs_expires_at
    ON export_jobs(expires_at);

ALTER TABLE export_jobs ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'export_jobs'
          AND policyname = 'Allow authenticated read access on export_jobs'
    ) THEN
        CREATE POLICY "Allow authenticated read access on export_jobs"
            ON export_jobs FOR SELECT
            TO authenticated
            USING (true);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'export_jobs'
          AND policyname = 'Allow service role full access on export_jobs'
    ) THEN
        CREATE POLICY "Allow service role full access on export_jobs"
            ON export_jobs FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

