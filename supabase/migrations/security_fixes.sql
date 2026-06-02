-- ============================================================
-- Security Fixes
-- 1. Enable RLS on check_updates (was missing)
-- 2. Fix views to use SECURITY INVOKER (not SECURITY DEFINER)
-- ============================================================

-- ==================== 1. CHECK UPDATES RLS ====================

ALTER TABLE check_updates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can read check_updates" ON check_updates;

CREATE POLICY "Anyone can read check_updates" ON check_updates
    FOR SELECT USING (true);

-- ==================== 2. VIEWS SECURITY INVOKER ====================
-- ALTER VIEW ... SET (security_invoker = true) é necessário porque
-- CREATE OR REPLACE VIEW não altera a segurança de views existentes

ALTER VIEW roi_summary_7days SET (security_invoker = true);
ALTER VIEW upcoming_scheduled_tasks SET (security_invoker = true);
ALTER VIEW default_tool_configurations SET (security_invoker = true);
