-- RM26-032: Storage policies for exports bucket
-- Goal: ZIP export files accessible only by requester client or authorized staff.

-- Ensure exports bucket exists and is private by default.
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'exports',
    'exports',
    FALSE,
    52428800,
    ARRAY['application/zip']::text[]
)
ON CONFLICT (id) DO UPDATE
SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Helper functions (idempotent) in case migration 004 wasn't applied yet.
CREATE OR REPLACE FUNCTION public.rm_request_role()
RETURNS text
LANGUAGE sql
STABLE
AS $$
    SELECT lower(
        coalesce(
            auth.jwt() ->> 'role',
            auth.jwt() -> 'app_metadata' ->> 'role',
            auth.jwt() -> 'user_metadata' ->> 'role',
            'authenticated'
        )
    );
$$;

CREATE OR REPLACE FUNCTION public.rm_request_client_id()
RETURNS text
LANGUAGE sql
STABLE
AS $$
    SELECT lower(
        coalesce(
            auth.jwt() ->> 'client_id',
            auth.jwt() -> 'app_metadata' ->> 'client_id',
            auth.jwt() -> 'user_metadata' ->> 'client_id',
            ''
        )
    );
$$;

-- Path convention for exports:
-- exports/{requester_client_uuid}/{filename}.zip
CREATE OR REPLACE FUNCTION public.rm_exports_object_client_id(object_name text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT lower(split_part(object_name, '/', 1));
$$;

DROP POLICY IF EXISTS "RM26 exports service role full" ON storage.objects;
DROP POLICY IF EXISTS "RM26 exports staff read" ON storage.objects;
DROP POLICY IF EXISTS "RM26 exports staff write" ON storage.objects;
DROP POLICY IF EXISTS "RM26 exports staff update" ON storage.objects;
DROP POLICY IF EXISTS "RM26 exports staff delete" ON storage.objects;
DROP POLICY IF EXISTS "RM26 exports client read own" ON storage.objects;
DROP POLICY IF EXISTS "RM26 exports client write own" ON storage.objects;
DROP POLICY IF EXISTS "RM26 exports client update own" ON storage.objects;
DROP POLICY IF EXISTS "RM26 exports client delete own" ON storage.objects;

CREATE POLICY "RM26 exports service role full"
    ON storage.objects
    FOR ALL
    TO service_role
    USING (bucket_id = 'exports')
    WITH CHECK (bucket_id = 'exports');

CREATE POLICY "RM26 exports staff read"
    ON storage.objects
    FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'exports'
        AND public.rm_request_role() IN ('admin', 'staff', 'operator', 'reviewer')
    );

CREATE POLICY "RM26 exports staff write"
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'exports'
        AND public.rm_request_role() IN ('admin', 'staff', 'operator', 'reviewer')
    );

CREATE POLICY "RM26 exports staff update"
    ON storage.objects
    FOR UPDATE
    TO authenticated
    USING (
        bucket_id = 'exports'
        AND public.rm_request_role() IN ('admin', 'staff', 'operator', 'reviewer')
    )
    WITH CHECK (
        bucket_id = 'exports'
        AND public.rm_request_role() IN ('admin', 'staff', 'operator', 'reviewer')
    );

CREATE POLICY "RM26 exports staff delete"
    ON storage.objects
    FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'exports'
        AND public.rm_request_role() IN ('admin', 'staff', 'operator', 'reviewer')
    );

CREATE POLICY "RM26 exports client read own"
    ON storage.objects
    FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'exports'
        AND public.rm_request_role() = 'client'
        AND public.rm_exports_object_client_id(name) = public.rm_request_client_id()
    );

CREATE POLICY "RM26 exports client write own"
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'exports'
        AND public.rm_request_role() = 'client'
        AND public.rm_exports_object_client_id(name) = public.rm_request_client_id()
    );

CREATE POLICY "RM26 exports client update own"
    ON storage.objects
    FOR UPDATE
    TO authenticated
    USING (
        bucket_id = 'exports'
        AND public.rm_request_role() = 'client'
        AND public.rm_exports_object_client_id(name) = public.rm_request_client_id()
    )
    WITH CHECK (
        bucket_id = 'exports'
        AND public.rm_request_role() = 'client'
        AND public.rm_exports_object_client_id(name) = public.rm_request_client_id()
    );

CREATE POLICY "RM26 exports client delete own"
    ON storage.objects
    FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'exports'
        AND public.rm_request_role() = 'client'
        AND public.rm_exports_object_client_id(name) = public.rm_request_client_id()
    );

