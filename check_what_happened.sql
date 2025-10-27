-- Check what's in the archive
SELECT 
    int_reference,
    source_type,
    created_by,
    created_at,
    email_id,
    whatsapp_id
FROM case_profile_migration_archive
WHERE created_by NOT IN ('MIGRATION_SCRIPT', 'RENUMBER_SCRIPT')
   OR created_at >= '2025-10-20'
ORDER BY created_at DESC
LIMIT 20;
