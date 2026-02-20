-- Migration: Add document_type enum and column to documents table
-- Date: 2026-02-12
-- Description: Adds document_type classification for TASA and PASSPORT_NIE documents

-- Create document_type enum
CREATE TYPE document_type AS ENUM (
    'TASA',
    'PASSPORT_NIE'
);

-- Add document_type column (nullable initially for existing rows)
ALTER TABLE documents 
ADD COLUMN document_type document_type;

-- For existing documents, you may need to classify them manually or set a default
-- UPDATE documents SET document_type = 'TASA' WHERE ...;
-- UPDATE documents SET document_type = 'PASSPORT_NIE' WHERE ...;

-- Add unique constraint to enforce one document per type per client
-- Note: This will fail if you have duplicate types for same client
-- Clean up duplicates first if needed
ALTER TABLE documents 
ADD CONSTRAINT unique_client_document_type UNIQUE (client_id, document_type);

-- Make document_type NOT NULL for future inserts (uncomment after backfilling existing data)
-- ALTER TABLE documents ALTER COLUMN document_type SET NOT NULL;
