-- ============================================================
-- PASO 2: ACTUALIZAR CLIENTES EXISTENTES
-- ============================================================
-- Ejecute este SQL DESPUÉS de completar el Paso 1

-- Ver todos los clientes que necesitan actualización
SELECT id, phone_number, name, passport_or_nie 
FROM clients 
ORDER BY created_at DESC;

-- Opción A: Actualizar UN cliente específico (recomendado para producción)
-- Reemplace los valores con datos reales de cada cliente:
-- UPDATE clients 
-- SET passport_or_nie = 'X1234567A'  -- Reemplace con NIE/Pasaporte real
-- WHERE id = 'client-id-aqui';

-- Opción B: Actualizar TODOS los clientes con valor temporal (solo para testing)
-- Descomente la siguiente línea si quiere marcar todos como pendientes:
-- UPDATE clients SET passport_or_nie = 'PENDING-TEMP' WHERE passport_or_nie = 'PENDING';

-- Para el cliente de prueba conocido:
UPDATE clients 
SET passport_or_nie = 'X1234567A'  -- Ejemplo NIE para pruebas
WHERE id = 'd78f4683-a2c4-408a-aee6-bc6be6b1df79';

-- Verificar los cambios:
SELECT id, phone_number, name, passport_or_nie 
FROM clients 
WHERE id = 'd78f4683-a2c4-408a-aee6-bc6be6b1df79';
