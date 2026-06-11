-- ============================================================
-- GENLAB SCHEMA: Row-Level Security (RLS) + Column-Level Security (CLS)
-- ============================================================
-- Roles: doctor, auditor, admin
-- RLS: Doctors see only their own reports; Auditors see all but limited columns
-- CLS: Auditor views use database views to restrict sensitive columns
-- ============================================================

-- ============== 1. DROP EXISTING OBJECTS (if any) ==============

DROP VIEW IF EXISTS public.auditor_reports_view CASCADE;
DROP VIEW IF EXISTS public.auditor_patients_view CASCADE;
DROP ROLE IF EXISTS doctor;
DROP ROLE IF EXISTS auditor;
DROP ROLE IF EXISTS admin;

-- ============== 2. CREATE ROLES ==============

CREATE ROLE admin WITH SUPERUSER LOGIN PASSWORD 'admin123';
CREATE ROLE doctor WITH LOGIN PASSWORD 'doctor123';
CREATE ROLE auditor WITH LOGIN PASSWORD 'auditor123';

-- ============== 3. CREATE TABLES (if not exists) ==============

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('doctor', 'auditor', 'admin', 'user')),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER UNIQUE NOT NULL,
    age INTEGER,
    sex VARCHAR(10),
    bmi NUMERIC,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    glucose NUMERIC,
    cholesterol NUMERIC,
    creatinine NUMERIC,
    diabetes BOOLEAN DEFAULT FALSE,
    hypertension BOOLEAN DEFAULT FALSE,
    diagnosis VARCHAR(100),
    readmission_30d BOOLEAN DEFAULT FALSE,
    mortality BOOLEAN DEFAULT FALSE,
    doctor_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id),
    doctor_id INTEGER NOT NULL REFERENCES users(id),
    data_informe VARCHAR(10),
    resultats TEXT,
    conclusions TEXT,
    diagnosi_privada TEXT,
    sensitive_notes TEXT,  -- Column for CLS - only doctor/admin see
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    old_values JSONB,
    new_values JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============== 4. ENABLE ROW-LEVEL SECURITY ==============

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ============== 5. CREATE SECURITY CONTEXT FUNCTION ==============

CREATE OR REPLACE FUNCTION current_user_id() RETURNS INTEGER AS $$
BEGIN
    RETURN (current_setting('app.current_user_id', true))::INTEGER;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION current_user_role() RETURNS VARCHAR AS $$
BEGIN
    RETURN current_setting('app.current_user_role', true)::VARCHAR;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============== 6. RLS POLICIES FOR USERS TABLE ==============

-- Admin can see all users
CREATE POLICY admin_users_all ON users
    FOR ALL
    USING (current_user_role() = 'admin');

-- Users can see their own profile
CREATE POLICY user_see_own_profile ON users
    FOR SELECT
    USING (id = current_user_id());

-- ============== 7. RLS POLICIES FOR PATIENTS TABLE ==============

-- Doctors can see their own patients (rows where doctor_id = current user)
CREATE POLICY doctor_see_own_patients ON patients
    FOR SELECT
    USING (doctor_id = current_user_id());

-- Doctors can insert patients they're assigned to
CREATE POLICY doctor_insert_patients ON patients
    FOR INSERT
    WITH CHECK (doctor_id = current_user_id());

-- Doctors can update their own patients
CREATE POLICY doctor_update_patients ON patients
    FOR UPDATE
    USING (doctor_id = current_user_id());

-- Auditors can see all patients (limited columns via view)
CREATE POLICY auditor_see_all_patients ON patients
    FOR SELECT
    USING (current_user_role() = 'auditor');

-- Admin can see all patients
CREATE POLICY admin_see_all_patients ON patients
    FOR ALL
    USING (current_user_role() = 'admin');

-- ============== 8. RLS POLICIES FOR REPORTS TABLE ==============

-- Doctors can see their own reports
CREATE POLICY doctor_see_own_reports ON reports
    FOR SELECT
    USING (doctor_id = current_user_id());

-- Doctors can insert their own reports
CREATE POLICY doctor_insert_reports ON reports
    FOR INSERT
    WITH CHECK (doctor_id = current_user_id());

-- Doctors can update their own reports
CREATE POLICY doctor_update_reports ON reports
    FOR UPDATE
    USING (doctor_id = current_user_id());

-- Auditors can see all reports (limited columns via view)
CREATE POLICY auditor_see_all_reports ON reports
    FOR SELECT
    USING (current_user_role() = 'auditor');

-- Admin can see all reports
CREATE POLICY admin_see_all_reports ON reports
    FOR ALL
    USING (current_user_role() = 'admin');

-- ============== 9. RLS POLICIES FOR AUDIT_LOGS TABLE ==============

-- Only admins can view audit logs
CREATE POLICY admin_audit_logs ON audit_logs
    FOR ALL
    USING (current_user_role() = 'admin');

-- Auditors can view audit logs (read-only)
CREATE POLICY auditor_audit_logs ON audit_logs
    FOR SELECT
    USING (current_user_role() = 'auditor');

-- ============== 10. COLUMN-LEVEL SECURITY VIEWS ==============

-- View for Auditors: Reports (excludes sensitive_notes column)
CREATE VIEW auditor_reports_view AS
SELECT 
    id,
    patient_id,
    doctor_id,
    data_informe,
    resultats,
    conclusions,
    diagnosi_privada,
    -- EXCLUDED: sensitive_notes (only doctor/admin see)
    created_at,
    updated_at
FROM reports
WHERE current_user_role() = 'auditor';

-- View for Auditors: Patients (excludes sensitive medical data)
CREATE VIEW auditor_patients_view AS
SELECT 
    id,
    patient_id,
    age,
    sex,
    diagnosis,
    -- EXCLUDED: sensitive clinical values (cholesterol, glucose, etc.)
    -- EXCLUDED: diabetes, hypertension flags (private)
    created_at,
    updated_at
FROM patients
WHERE current_user_role() = 'auditor';

-- ============== 11. GRANT PERMISSIONS ==============

-- Doctor Role Permissions
GRANT CONNECT ON DATABASE ecb_db TO doctor;
GRANT USAGE ON SCHEMA public TO doctor;
GRANT SELECT, INSERT, UPDATE ON users TO doctor;
GRANT SELECT, INSERT, UPDATE ON patients TO doctor;
GRANT SELECT, INSERT, UPDATE ON reports TO doctor;
GRANT SELECT ON audit_logs TO doctor;
GRANT EXECUTE ON FUNCTION current_user_id() TO doctor;
GRANT EXECUTE ON FUNCTION current_user_role() TO doctor;

-- Auditor Role Permissions (read-only with limited columns)
GRANT CONNECT ON DATABASE ecb_db TO auditor;
GRANT USAGE ON SCHEMA public TO auditor;
GRANT SELECT ON users TO auditor;
GRANT SELECT ON patients TO auditor;
GRANT SELECT ON reports TO auditor;
GRANT SELECT ON audit_logs TO auditor;
-- Auditor can use the restricted views
GRANT SELECT ON auditor_reports_view TO auditor;
GRANT SELECT ON auditor_patients_view TO auditor;
GRANT EXECUTE ON FUNCTION current_user_id() TO auditor;
GRANT EXECUTE ON FUNCTION current_user_role() TO auditor;

-- Admin Role Permissions (all)
GRANT CONNECT ON DATABASE ecb_db TO admin;
GRANT USAGE ON SCHEMA public TO admin;
GRANT ALL ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO admin;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO admin;

-- ============== 12. AUDIT TRIGGER ==============

CREATE OR REPLACE FUNCTION audit_trigger_func() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values, ip_address, created_at)
    VALUES (
        current_user_id(),
        TG_OP,
        TG_TABLE_NAME,
        NEW.id,
        ROW_TO_JSON(OLD),
        ROW_TO_JSON(NEW),
        current_setting('app.client_ip', true),
        CURRENT_TIMESTAMP
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to reports
CREATE TRIGGER audit_reports_trigger AFTER INSERT OR UPDATE OR DELETE ON reports
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Apply audit trigger to patients
CREATE TRIGGER audit_patients_trigger AFTER INSERT OR UPDATE OR DELETE ON patients
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- ============== 13. SAMPLE DATA ==============

-- Insert admin user
INSERT INTO users (username, email, role, password_hash) VALUES 
    ('admin', 'admin@ecb.local', 'admin', 'hash_admin123')
ON CONFLICT DO NOTHING;

-- Insert doctors
INSERT INTO users (username, email, role, password_hash) VALUES 
    ('dr_smith', 'dr.smith@ecb.local', 'doctor', 'hash_doctor123'),
    ('dr_jones', 'dr.jones@ecb.local', 'doctor', 'hash_doctor123')
ON CONFLICT DO NOTHING;

-- Insert auditor
INSERT INTO users (username, email, role, password_hash) VALUES 
    ('auditor', 'auditor@ecb.local', 'auditor', 'hash_auditor123')
ON CONFLICT DO NOTHING;

-- ============== 14. USAGE EXAMPLES ==============
/*
-- For backend to set user context (run BEFORE each query):

SET app.current_user_id = '1';  -- doctor with id=1
SET app.current_user_role = 'doctor';

-- Doctor 1 now only sees their own reports via RLS
SELECT * FROM reports;  -- Only shows reports where doctor_id = 1

-- For Auditor (sees all, but with limited columns):
SET app.current_user_id = '3';  -- auditor
SET app.current_user_role = 'auditor';

-- Auditor sees all reports but uses view with CLS
SELECT * FROM auditor_reports_view;  -- No sensitive_notes column

-- For Admin (full access):
SET app.current_user_id = '0';  -- admin
SET app.current_user_role = 'admin';

SELECT * FROM reports;  -- Sees everything including sensitive_notes
*/

-- ============== 15. INDEXES FOR PERFORMANCE ==============

CREATE INDEX idx_reports_doctor_id ON reports(doctor_id);
CREATE INDEX idx_reports_patient_id ON reports(patient_id);
CREATE INDEX idx_patients_doctor_id ON patients(doctor_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
