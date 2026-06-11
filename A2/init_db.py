import asyncio
from database import init_db, engine
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def apply_rls_policies():
    """Apply RLS policies to existing tables"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='ecb_user',
        password='ecb_password',
        database='ecb_db'
    )
    
    try:
        # Enable RLS
        await conn.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
        await conn.execute("ALTER TABLE patients ENABLE ROW LEVEL SECURITY;")
        await conn.execute("ALTER TABLE reports ENABLE ROW LEVEL SECURITY;")
        await conn.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;")
        await conn.execute("ALTER TABLE medical_files ENABLE ROW LEVEL SECURITY;")
        
        # Drop existing policies if they exist
        policies = [
            ("reports", "doctor_reports_policy"),
            ("reports", "admin_reports_all_policy"),
            ("patients", "doctor_patients_policy"),
            ("patients", "admin_patients_all_policy"),
            ("medical_files", "doctor_files_policy"),
            ("medical_files", "admin_files_all_policy"),
        ]
        
        for table, policy in policies:
            try:
                await conn.execute(f"DROP POLICY IF EXISTS {policy} ON {table};")
            except:
                pass
        
        # Create RLS policies
        # Doctors can only see their own reports
        await conn.execute("""
            CREATE POLICY doctor_reports_policy ON reports
                FOR SELECT
                USING (doctor_id IN (SELECT id FROM users WHERE username = current_user))
        """)
        
        # Admins can see all reports
        await conn.execute("""
            CREATE POLICY admin_reports_all_policy ON reports
                FOR ALL
                USING (true)
        """)
        
        # Doctors can see their own patients
        await conn.execute("""
            CREATE POLICY doctor_patients_policy ON patients
                FOR SELECT
                USING (doctor_id IN (SELECT id FROM users WHERE username = current_user))
        """)
        
        # Admins can see all patients
        await conn.execute("""
            CREATE POLICY admin_patients_all_policy ON patients
                FOR ALL
                USING (true)
        """)
        
        # Doctors can see files for their own patients
        await conn.execute("""
            CREATE POLICY doctor_files_policy ON medical_files
                FOR SELECT
                USING (
                    patient_id IN (
                        SELECT id FROM patients 
                        WHERE doctor_id IN (SELECT id FROM users WHERE username = current_user)
                    )
                )
        """)
        
        # Admins can see all files
        await conn.execute("""
            CREATE POLICY admin_files_all_policy ON medical_files
                FOR ALL
                USING (true)
        """)
        
        print("✅ RLS policies applied successfully!")
        
    except Exception as e:
        print(f"⚠️  {e}")
    finally:
        await conn.close()

async def main():
    """Initialize database"""
    print("Creating tables...")
    await init_db()
    print("✅ Tables created!")
    
    print("Applying RLS policies...")
    await apply_rls_policies()

if __name__ == "__main__":
    asyncio.run(main())

