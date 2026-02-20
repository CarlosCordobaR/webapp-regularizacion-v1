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
