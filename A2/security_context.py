"""
Security Context Manager for PostgreSQL RLS/CLS
Handles setting user context for Row-Level and Column-Level Security
"""

from typing import Optional, Literal
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SecurityContext:
    """Manages database security context for RLS/CLS"""
    
    def __init__(self, session: AsyncSession, user_id: int, role: Literal["admin", "doctor", "auditor", "user"]):
        """
        Initialize security context
        
        Args:
            session: AsyncSession database connection
            user_id: User ID for RLS policies
            role: User role (admin, doctor, auditor, user)
        """
        self.session = session
        self.user_id = user_id
        self.role = role
    
    async def set_context(self) -> None:
        """Set PostgreSQL session context for RLS/CLS policies"""
        await self.session.execute(text(f"SET app.current_user_id = '{self.user_id}'"))
        await self.session.execute(text(f"SET app.current_user_role = '{self.role}'"))
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.set_context()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass


# ============================================================================
# Query Helpers
# ============================================================================

async def get_user_reports(session: AsyncSession, user_id: int, role: str):
    """
    Get reports with proper RLS/CLS applied
    
    Doctor: Only their own reports
    Auditor: All reports with limited columns (via view)
    Admin: All reports with all columns
    """
    async with SecurityContext(session, user_id, role):
        if role == "auditor":
            # Auditors use the CLS view to avoid seeing sensitive columns
            query = text("SELECT * FROM auditor_reports_view")
        else:
            # Doctor/Admin see the full table (RLS filters for doctor)
            query = text("SELECT * FROM reports")
        
        result = await session.execute(query)
        return result.fetchall()


async def get_user_patients(session: AsyncSession, user_id: int, role: str):
    """
    Get patients with proper RLS/CLS applied
    
    Doctor: Only their own patients
    Auditor: All patients with limited columns (via view)
    Admin: All patients with all columns
    """
    async with SecurityContext(session, user_id, role):
        if role == "auditor":
            # Auditors use the CLS view to avoid seeing sensitive columns
            query = text("SELECT * FROM auditor_patients_view")
        else:
            # Doctor/Admin see the full table (RLS filters for doctor)
            query = text("SELECT * FROM patients")
        
        result = await session.execute(query)
        return result.fetchall()


async def create_report(
    session: AsyncSession,
    user_id: int,
    role: str,
    patient_id: int,
    doctor_id: int,
    resultats: str,
    conclusions: str,
    diagnosi_privada: Optional[str] = None,
    sensitive_notes: Optional[str] = None,
) -> dict:
    """
    Create a report with RLS enforcement
    
    Only doctors can create reports for themselves (doctor_id must be current user)
    Admin can create for any doctor
    """
    async with SecurityContext(session, user_id, role):
        query = text("""
            INSERT INTO reports 
            (patient_id, doctor_id, resultats, conclusions, diagnosi_privada, sensitive_notes)
            VALUES (:patient_id, :doctor_id, :resultats, :conclusions, :diagnosi_privada, :sensitive_notes)
            RETURNING *
        """)
        
        result = await session.execute(query, {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "resultats": resultats,
            "conclusions": conclusions,
            "diagnosi_privada": diagnosi_privada,
            "sensitive_notes": sensitive_notes,
        })
        
        await session.commit()
        return dict(result.first())


async def get_audit_logs(
    session: AsyncSession,
    user_id: int,
    role: str,
    table_name: Optional[str] = None,
    limit: int = 100
) -> list:
    """
    Get audit logs with RLS enforcement
    
    Only admin can view full audit logs
    Auditors can view logs for their review
    Doctors cannot view audit logs
    """
    async with SecurityContext(session, user_id, role):
        if role not in ("admin", "auditor"):
            return []
        
        where_clause = f"WHERE table_name = '{table_name}'" if table_name else ""
        query = text(f"""
            SELECT * FROM audit_logs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        result = await session.execute(query, {"limit": limit})
        return [dict(row) for row in result.fetchall()]


# ============================================================================
# Middleware for FastAPI
# ============================================================================

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RLSMiddleware(BaseHTTPMiddleware):
    """Middleware to set RLS context for each request"""
    
    async def dispatch(self, request: Request, call_next):
        # Extract user info from JWT token or session
        # This is a simplified example
        user_id = request.headers.get("X-User-ID")
        user_role = request.headers.get("X-User-Role")
        
        if not user_id or not user_role:
            # Try to get from session/JWT
            # In real implementation, decode JWT token here
            pass
        
        # Store in request state for use in routes
        if user_id and user_role:
            request.state.user_id = int(user_id)
            request.state.user_role = user_role
        
        response = await call_next(request)
        return response


# ============================================================================
# Example FastAPI Routes
# ============================================================================

"""
# In your FastAPI app:

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

# Add RLS middleware
app.add_middleware(RLSMiddleware)

@app.get("/api/reports")
async def get_reports(
    request: Request,
    session: AsyncSession = Depends(get_db_session)
):
    '''Get reports with RLS/CLS applied'''
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    reports = await get_user_reports(
        session,
        request.state.user_id,
        request.state.user_role
    )
    return reports


@app.get("/api/patients")
async def get_patients(
    request: Request,
    session: AsyncSession = Depends(get_db_session)
):
    '''Get patients with RLS/CLS applied'''
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    patients = await get_user_patients(
        session,
        request.state.user_id,
        request.state.user_role
    )
    return patients


@app.post("/api/reports")
async def create_new_report(
    request: Request,
    report_data: dict,
    session: AsyncSession = Depends(get_db_session)
):
    '''Create report with RLS enforcement'''
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Doctor can only create for themselves
    if request.state.user_role == "doctor":
        report_data["doctor_id"] = request.state.user_id
    elif request.state.user_role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    report = await create_report(
        session,
        request.state.user_id,
        request.state.user_role,
        **report_data
    )
    return report


@app.get("/api/audit-logs")
async def get_logs(
    request: Request,
    table_name: str = None,
    session: AsyncSession = Depends(get_db_session)
):
    '''Get audit logs with RLS enforcement'''
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    logs = await get_audit_logs(
        session,
        request.state.user_id,
        request.state.user_role,
        table_name
    )
    return logs
"""
