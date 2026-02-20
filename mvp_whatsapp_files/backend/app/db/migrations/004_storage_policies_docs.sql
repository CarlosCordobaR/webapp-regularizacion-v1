-- RM26-031: Storage policies for client documents bucket
-- Scope: bucket client-documents (rm2026-docs equivalent in current app config)
-- Goals:
-- 1) service_role full access
-- 2) authenticated staff access by role
-- 3) authenticated client access only to own case files (client_id embedded in path)

-- Ensure bucket exists and is private by default.
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'client-documents',
    'client-documents',
    FALSE,
    10485760,
    ARRAY['application/pdf']::text[]
)
ON CONFLICT (id) DO UPDATE
SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Helpers for policy evaluation from JWT claims.
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

-- Path convention currently used by backend:
-- profiles/{profile}/{client_name}_{client_uuid}/{timestamp}_{filename}.pdf
CREATE OR REPLACE FUNCTION public.rm_storage_object_client_id(object_name text)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT lower(right(split_part(object_name, '/', 3), 36));
$$;

-- Drop and recreate policies idempotently.
DROP POLICY IF EXISTS "RM26 docs service role full" ON storage.objects;
DROP POLICY IF EXISTS "RM26 docs staff read" ON storage.objects;
DROP POLICY IF EXISTS "RM26 docs staff write" ON storage.objects;
DROP POLICY IF EXISTS "RM26 docs staff update" ON storage.objects;
DROP POLICY IF EXISTS "RM26 docs staff delete" ON storage.objects;
DROP POLICY IF EXISTS "RM26 docs client read own case" ON storage.objects;
DROP POLICY IF EXISTS "RM26 docs client write own case" ON storage.objects;
DROP POLICY IF EXISTS "RM26 docs client update own case" ON storage.objects;
DROP POLICY IF EXISTS "RM26 docs client delete own case" ON storage.objects;

CREATE POLICY "RM26 docs service role full"
    ON storage.objects
    FOR ALL
    TO service_role
    USING (bucket_id = 'client-documents')
    WITH CHECK (bucket_id = 'client-documents');

CREATE POLICY "RM26 docs staff read"
    ON storage.objects
    FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'client-documents'
        AND public.rm_request_role() IN ('admin', 'staff', 'operator', 'reviewer')
    );

CREATE POLICY "RM26 docs staff write"
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'client-documents'
        AND public.rm_request_role() IN ('admin', 'staff', 'operator', 'reviewer')
    );

CREATE POLICY "RM26 docs staff update"
    ON storage.objects
    FOR UPDATE
    TO authenticated
    USING (
        bucket_id = 'client-documents'
        AND public.rm_request_role() IN ('admin', 'staff', 'operator', 'reviewer')
    )
    WITH CHECK (
        bucket_id = 'client-documents'
        AND public.rm_request_role() IN ('admin', 'staff', 'operator', 'reviewer')
    );

CREATE POLICY "RM26 docs staff delete"
    ON storage.objects
    FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'client-documents'
        AND public.rm_request_role() IN ('admin', 'staff', 'operator', 'reviewer')
    );

CREATE POLICY "RM26 docs client read own case"
    ON storage.objects
    FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'client-documents'
        AND public.rm_request_role() = 'client'
        AND public.rm_storage_object_client_id(name) = public.rm_request_client_id()
    );

CREATE POLICY "RM26 docs client write own case"
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'client-documents'
        AND public.rm_request_role() = 'client'
        AND public.rm_storage_object_client_id(name) = public.rm_request_client_id()
    );

CREATE POLICY "RM26 docs client update own case"
    ON storage.objects
    FOR UPDATE
    TO authenticated
    USING (
        bucket_id = 'client-documents'
        AND public.rm_request_role() = 'client'
        AND public.rm_storage_object_client_id(name) = public.rm_request_client_id()
    )
    WITH CHECK (
        bucket_id = 'client-documents'
        AND public.rm_request_role() = 'client'
        AND public.rm_storage_object_client_id(name) = public.rm_request_client_id()
    );

CREATE POLICY "RM26 docs client delete own case"
    ON storage.objects
    FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'client-documents'
        AND public.rm_request_role() = 'client'
        AND public.rm_storage_object_client_id(name) = public.rm_request_client_id()
    );

