-- ============== Create PostgreSQL Roles ==============

-- Create roles if they don't exist
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'doctor') THEN
        CREATE ROLE doctor;
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'auditor') THEN
        CREATE ROLE auditor;
    END IF;
END $$;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin') THEN
        CREATE ROLE admin SUPERUSER;
    END IF;
END $$;

-- ============== Enable RLS ==============

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ============== RLS Policies for Reports ==============

-- Doctors can only see their own reports
CREATE POLICY doctor_reports_policy ON reports
    FOR SELECT
    USING (doctor_id = current_user_id());

CREATE POLICY doctor_insert_reports_policy ON reports
    FOR INSERT
    WITH CHECK (doctor_id = current_user_id());

CREATE POLICY doctor_update_reports_policy ON reports
    FOR UPDATE
    USING (doctor_id = current_user_id());

-- Admins can see all reports
CREATE POLICY admin_reports_all_policy ON reports
    FOR ALL
    USING (current_setting('request.user.role') = 'admin');

-- Auditors can only see reports (read-only)
CREATE POLICY auditor_reports_policy ON reports
    FOR SELECT
    USING (current_setting('request.user.role') = 'auditor');

-- ============== RLS Policies for Patients ==============

-- Doctors can see their own patients
CREATE POLICY doctor_patients_policy ON patients
    FOR SELECT
    USING (doctor_id = current_user_id());

-- Admins can see all patients
CREATE POLICY admin_patients_all_policy ON patients
    FOR ALL
    USING (current_setting('request.user.role') = 'admin');

-- ============== Grant Permissions ==============

GRANT CONNECT ON DATABASE ecb_db TO doctor;
GRANT CONNECT ON DATABASE ecb_db TO auditor;
GRANT CONNECT ON DATABASE ecb_db TO admin;

-- Doctor permissions
GRANT SELECT, INSERT, UPDATE ON users TO doctor;
GRANT SELECT, INSERT, UPDATE ON patients TO doctor;
GRANT SELECT, INSERT, UPDATE ON reports TO doctor;

-- Auditor permissions (read-only)
GRANT SELECT ON users TO auditor;
GRANT SELECT ON patients TO auditor;
GRANT SELECT ON reports TO auditor;

-- Admin permissions (all)
GRANT ALL ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO admin;
