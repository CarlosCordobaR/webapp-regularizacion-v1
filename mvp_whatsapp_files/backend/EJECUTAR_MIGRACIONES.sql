-- ============================================================
-- PASO 1: EJECUTAR MIGRACIONES
-- ============================================================
-- Copie y pegue este SQL completo en el editor que acaba de abrirse
-- Luego presione el botón RUN

-- Migration 1: Add passport_or_nie field to clients table
ALTER TABLE clients 
ADD COLUMN passport_or_nie TEXT DEFAULT 'PENDING';

ALTER TABLE clients 
ALTER COLUMN passport_or_nie SET NOT NULL;

-- Migration 2: Add document_type enum and column to documents table
CREATE TYPE document_type AS ENUM (
    'TASA',
    'PASSPORT_NIE'
);

ALTER TABLE documents 
ADD COLUMN document_type document_type;

ALTER TABLE documents 
ADD CONSTRAINT unique_client_document_type UNIQUE (client_id, document_type);

-- ============================================================
-- Verificación (ejecute esto después para confirmar)
-- ============================================================
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'clients' AND column_name = 'passport_or_nie';

-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'documents' AND column_name = 'document_type';
