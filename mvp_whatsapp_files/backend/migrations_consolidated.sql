-- Consolidated migrations for expediente feature
-- Generated: /Users/PhD/Desktop/WebApp_Regularizacion_1/mvp_whatsapp_files/backend
-- Execute this entire file in Supabase SQL Editor


-- ============================================================
-- 001_add_passport_or_nie.sql
-- ============================================================

-- Migration: Add passport_or_nie field to clients table
-- Date: 2026-02-12
-- Description: Adds required passport_or_nie field for expediente generation

-- Add column with a default value for existing rows
ALTER TABLE clients 
ADD COLUMN passport_or_nie TEXT DEFAULT 'PENDING';

-- Update existing rows to remove default (set to actual value or 'PENDING')
-- In production, you should update existing rows with real values before making NOT NULL

-- Make column NOT NULL for new inserts
ALTER TABLE clients 
ALTER COLUMN passport_or_nie SET NOT NULL;

-- Note: If you have existing clients, update them first:
-- UPDATE clients SET passport_or_nie = 'ACTUAL_VALUE' WHERE id = 'client_id';



-- ============================================================
-- 002_add_document_type.sql
-- ============================================================

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


