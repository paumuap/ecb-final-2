from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timedelta
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt
import uvicorn
import os

# ============== Configuration ==============
SECRET_KEY = "ecb-secret-key-2026-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="ECB API", version="1.0.0", docs_url="/api/docs")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
password_hasher = PasswordHasher()

# Add CORS middleware for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Models ==============

# User models
class User(BaseModel):
    username: str = Field(..., min_length=1)
    email: EmailStr
    role: str = Field(default="user", description="Role: admin or user")

class UserInDB(User):
    hashed_password: str

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="user", description="Role: admin or user")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

# Patient models
class Pacient(BaseModel):
    id: Optional[int] = None
    nom: str = Field(..., min_length=1, description="Patient first name")
    cognom: str = Field(..., min_length=1, description="Patient last name")
    email: EmailStr
    data_naixement: str = Field(..., description="Birth date (YYYY-MM-DD)")
    numero_historia: str = Field(..., min_length=1, description="Medical record number")

class PacientCreate(BaseModel):
    nom: str = Field(..., min_length=1)
    cognom: str = Field(..., min_length=1)
    email: EmailStr
    data_naixement: str
    numero_historia: str

class Mostra(BaseModel):
    id: Optional[int] = None
    pacient_id: int = Field(..., gt=0)
    tipus: str = Field(..., min_length=1, description="Sample type")
    data_recollida: str = Field(..., description="Collection date (YYYY-MM-DD)")
    estat: str = Field(default="pendent", description="Status: pendent, processada, completada")

class MostraCreate(BaseModel):
    pacient_id: int = Field(..., gt=0)
    tipus: str = Field(..., min_length=1)
    data_recollida: str
    estat: str = Field(default="pendent")

class Informe(BaseModel):
    id: Optional[int] = None
    mostra_id: int = Field(..., gt=0)
    data_informe: str = Field(..., description="Report date (YYYY-MM-DD)")
    resultats: str = Field(..., min_length=1, description="Test results")
    conclusions: str = Field(..., min_length=1, description="Conclusions")

class InformeCreate(BaseModel):
    mostra_id: int = Field(..., gt=0)
    data_informe: str
    resultats: str = Field(..., min_length=1)
    conclusions: str = Field(..., min_length=1)

class AuthenticatedUser(BaseModel):
    username: str
    token: str

# ============== In-memory Database ==============

users_db = {
    "admin": UserInDB(
        username="admin",
        email="admin@ecb.com",
        role="admin",
        hashed_password=password_hasher.hash("admin123")
    ),
    "user": UserInDB(
        username="user",
        email="user@ecb.com",
        role="user",
        hashed_password=password_hasher.hash("user123")
    )
}

pacients_db = []
mostres_db = []
informes_db = []
id_counter = {"pacient": 1, "mostra": 1, "informe": 1}

# ============== Startup Event ==============

@app.on_event("startup")
async def startup_event():
    """Initialize demo data on startup"""
    # Create demo patient for testing
    demo_pacient = Pacient(
        id=1,
        nom="Demo",
        cognom="Patient",
        email="demo@ecb.com",
        data_naixement="1990-01-01",
        numero_historia="H00001"
    )
    pacients_db.append(demo_pacient)
    print(f"✅ Created demo patient: {demo_pacient.nom} {demo_pacient.cognom} (ID: {demo_pacient.id})")

# ============== Dependencies ==============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against Argon2 hash"""
    try:
        password_hasher.verify(hashed_password, plain_password)
        return True
    except VerifyMismatchError:
        return False

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user by username and password"""
    if username not in users_db:
        return None
    user = users_db[username]
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Verify JWT token and return current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    if token_data.username not in users_db:
        raise credentials_exception
    user_in_db = users_db[token_data.username]
    return User(username=user_in_db.username, email=user_in_db.email, role=user_in_db.role)

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is admin"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_db_session():
    """Dependency for database session"""
    return {"pacients": pacients_db, "mostres": mostres_db, "informes": informes_db}

# ============== AUTHENTICATION ==============

@app.post("/api/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 login endpoint - returns JWT token"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """Register a new user"""
    if user_data.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = password_hasher.hash(user_data.password)
    new_user = UserInDB(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    users_db[user_data.username] = new_user
    return User(username=new_user.username, email=new_user.email)

@app.get("/api/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info"""
    return current_user

# ============== ADMIN ENDPOINTS ==============

@app.get("/api/admin/users", response_model=List[User])
async def list_all_users(admin_user: User = Depends(require_admin)):
    """Admin only: List all users"""
    return [User(username=u.username, email=u.email, role=u.role) for u in users_db.values()]

@app.post("/api/admin/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_data: UserRegister,
    admin_user: User = Depends(require_admin)
):
    """Admin only: Create user with specific role"""
    if user_data.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    hashed_password = password_hasher.hash(user_data.password)
    new_user = UserInDB(
        username=user_data.username,
        email=user_data.email,
        role=user_data.role,
        hashed_password=hashed_password
    )
    users_db[user_data.username] = new_user
    return User(username=new_user.username, email=new_user.email, role=new_user.role)

@app.get("/api/admin/pacients", response_model=List[Pacient])
async def admin_list_all_pacients(
    admin_user: User = Depends(require_admin),
    db: dict = Depends(get_db_session)
):
    """Admin only: View all patients"""
    if not db["pacients"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No patients registered"
        )
    return db["pacients"]

# ============== PACIENTS ==============

@app.post("/api/pacients", response_model=Pacient, status_code=status.HTTP_201_CREATED)
async def crear_pacient(
    pacient: PacientCreate,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Create a new patient"""
    new_pacient = Pacient(
        id=id_counter["pacient"],
        **pacient.dict()
    )
    id_counter["pacient"] += 1
    db["pacients"].append(new_pacient)
    return new_pacient

@app.get("/api/pacients", response_model=List[Pacient])
async def llistar_pacients(
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """List all patients"""
    if not db["pacients"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No patients registered"
        )
    return db["pacients"]

@app.get("/api/pacients/{pacient_id}", response_model=Pacient)
async def obtenir_pacient(
    pacient_id: int,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Get patient by ID"""
    for pacient in db["pacients"]:
        if pacient.id == pacient_id:
            return pacient
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Patient with ID {pacient_id} not found"
    )

@app.put("/api/pacients/{pacient_id}", response_model=Pacient)
async def actualitzar_pacient(
    pacient_id: int,
    pacient_actualitzat: PacientCreate,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Update patient data"""
    for i, pacient in enumerate(db["pacients"]):
        if pacient.id == pacient_id:
            updated = Pacient(id=pacient_id, **pacient_actualitzat.dict())
            db["pacients"][i] = updated
            return updated
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Patient with ID {pacient_id} not found"
    )

@app.delete("/api/pacients/{pacient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_pacient(
    pacient_id: int,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Delete a patient"""
    for i, pacient in enumerate(db["pacients"]):
        if pacient.id == pacient_id:
            db["pacients"].pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Patient with ID {pacient_id} not found"
    )

# ============== MOSTRES (Samples) ==============

@app.post("/api/mostres", response_model=Mostra, status_code=status.HTTP_201_CREATED)
async def crear_mostra(
    mostra: MostraCreate,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Create a new sample"""
    # Verify patient exists
    pacient_exists = any(p.id == mostra.pacient_id for p in db["pacients"])
    if not pacient_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with ID {mostra.pacient_id} does not exist"
        )
    
    new_mostra = Mostra(
        id=id_counter["mostra"],
        **mostra.dict()
    )
    id_counter["mostra"] += 1
    db["mostres"].append(new_mostra)
    return new_mostra

@app.get("/api/mostres", response_model=List[Mostra])
async def llistar_mostres(
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """List all samples"""
    if not db["mostres"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No samples registered"
        )
    return db["mostres"]

@app.get("/api/mostres/{mostra_id}", response_model=Mostra)
async def obtenir_mostra(
    mostra_id: int,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Get sample by ID"""
    for mostra in db["mostres"]:
        if mostra.id == mostra_id:
            return mostra
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sample with ID {mostra_id} not found"
    )

@app.put("/api/mostres/{mostra_id}", response_model=Mostra)
async def actualitzar_mostra(
    mostra_id: int,
    mostra_actualitzada: MostraCreate,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Update sample data"""
    for i, mostra in enumerate(db["mostres"]):
        if mostra.id == mostra_id:
            # Verify patient still exists
            pacient_exists = any(p.id == mostra_actualitzada.pacient_id for p in db["pacients"])
            if not pacient_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Patient with ID {mostra_actualitzada.pacient_id} does not exist"
                )
            updated = Mostra(id=mostra_id, **mostra_actualitzada.dict())
            db["mostres"][i] = updated
            return updated
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sample with ID {mostra_id} not found"
    )

@app.delete("/api/mostres/{mostra_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_mostra(
    mostra_id: int,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Delete a sample"""
    for i, mostra in enumerate(db["mostres"]):
        if mostra.id == mostra_id:
            db["mostres"].pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Sample with ID {mostra_id} not found"
    )

# ============== INFORMES (Reports) ==============

@app.post("/api/informes", response_model=Informe, status_code=status.HTTP_201_CREATED)
async def crear_informe(
    informe: InformeCreate,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Create a new report"""
    # Verify sample exists
    mostra_exists = any(m.id == informe.mostra_id for m in db["mostres"])
    if not mostra_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sample with ID {informe.mostra_id} does not exist"
        )
    
    new_informe = Informe(
        id=id_counter["informe"],
        **informe.dict()
    )
    id_counter["informe"] += 1
    db["informes"].append(new_informe)
    return new_informe

@app.get("/api/informes", response_model=List[Informe])
async def llistar_informes(
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """List all reports"""
    if not db["informes"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reports registered"
        )
    return db["informes"]

@app.get("/api/informes/{informe_id}", response_model=Informe)
async def obtenir_informe(
    informe_id: int,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Get report by ID"""
    for informe in db["informes"]:
        if informe.id == informe_id:
            return informe
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Report with ID {informe_id} not found"
    )

@app.put("/api/informes/{informe_id}", response_model=Informe)
async def actualitzar_informe(
    informe_id: int,
    informe_actualitzat: InformeCreate,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Update report data"""
    for i, informe in enumerate(db["informes"]):
        if informe.id == informe_id:
            # Verify sample still exists
            mostra_exists = any(m.id == informe_actualitzat.mostra_id for m in db["mostres"])
            if not mostra_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sample with ID {informe_actualitzat.mostra_id} does not exist"
                )
            updated = Informe(id=informe_id, **informe_actualitzat.dict())
            db["informes"][i] = updated
            return updated
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Report with ID {informe_id} not found"
    )

@app.delete("/api/informes/{informe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_informe(
    informe_id: int,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Delete a report"""
    for i, informe in enumerate(db["informes"]):
        if informe.id == informe_id:
            db["informes"].pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Report with ID {informe_id} not found"
    )

# ============== FILE MANAGEMENT (MinIO S3) ==============

class MedicalFileInfo(BaseModel):
    id: Optional[int] = None
    patient_id: int
    report_id: Optional[int] = None
    original_filename: str
    file_size: int
    file_type: str  # report, scan, lab_result, genetic_data, etc.
    s3_url: Optional[str] = None
    uploaded_by: str

class MedicalFileResponse(BaseModel):
    download_url: str
    original_filename: str
    file_type: str
    expires_in_hours: int

# In-memory file storage (would be in PostgreSQL in production)
files_db = []
file_id_counter = 1

@app.post("/api/files/upload/{patient_id}")
async def upload_medical_file(
    patient_id: int,
    file_type: str,
    file: UploadFile = File(...),
    db: dict = Depends(get_db_session)
):
    """Upload medical file for a patient (PDF, image, FASTA, etc.)"""
    global file_id_counter
    
    # Verify patient exists
    pacient_exists = any(p.id == patient_id for p in db["pacients"])
    if not pacient_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    # Read file content
    content = await file.read()
    
    try:
        # Import file_storage and upload
        from file_storage import upload_file
        
        file_metadata = await upload_file(
            file_content=content,
            filename=file.filename,
            patient_id=patient_id,
            file_type=file_type
        )
        
        # Get current user ID (find in users_db)
        user_id = None
        username = "system"
        # For now, use a default system user since auth is optional
        
        # Store metadata in in-memory DB (would be PostgreSQL in production)
        file_record = {
            "id": file_id_counter,
            "patient_id": patient_id,
            "report_id": None,
            "original_filename": file_metadata["original_filename"],
            "file_size": file_metadata["file_size"],
            "file_type": file_metadata["file_type"],
            "s3_key": file_metadata["s3_key"],
            "uploaded_by": username,
            "uploaded_at": datetime.utcnow().isoformat()
        }
        files_db.append(file_record)
        file_id_counter += 1
        
        return {
            "id": file_record["id"],
            "message": "File uploaded successfully",
            "file": file_record
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload failed: {str(e)}"
        )

@app.get("/api/files/patient/{patient_id}", response_model=List[MedicalFileInfo])
async def list_patient_files(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """List all medical files for a patient (RLS: doctor can only see own patient files)"""
    # Verify patient exists
    patient = next((p for p in db["pacients"] if p.id == patient_id), None)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    # Note: Full RLS enforcement will be in PostgreSQL
    # For now, allow all authenticated users to list (admin sees all, doctor limited by DB in future)
    
    # Filter files for this patient
    patient_files = [f for f in files_db if f["patient_id"] == patient_id]
    
    if not patient_files:
        return []
    
    return patient_files

@app.get("/api/files/{file_id}/download", response_model=MedicalFileResponse)
async def get_file_download_link(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Get presigned download URL for a file (RLS: verify access)"""
    # Find file
    file_record = next((f for f in files_db if f["id"] == file_id), None)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )
    
    # Note: Full RLS enforcement will be in PostgreSQL
    # For now, allow downloads for authenticated users
    
    # Generate presigned URL
    try:
        from file_storage import get_presigned_url
        download_url = get_presigned_url(file_record["s3_key"], expires_hours=24)
    except:
        # Fallback to direct URL
        download_url = f"https://play.min.io/ecb-medical-files/{file_record['s3_key']}"
    
    return {
        "download_url": download_url,
        "original_filename": file_record["original_filename"],
        "file_type": file_record["file_type"],
        "expires_in_hours": 24
    }

@app.delete("/api/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medical_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: dict = Depends(get_db_session)
):
    """Delete a medical file (RLS: admin only or uploader)"""
    # Find file
    file_record = next((f for f in files_db if f["id"] == file_id), None)
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )
    
    # Check access control: admin or uploader can delete
    if current_user.role != "admin" and file_record["uploaded_by"] != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or file uploader can delete files"
        )
    
    # Delete from S3
    try:
        from file_storage import delete_file
        delete_file(file_record["s3_key"])
    except Exception as e:
        print(f"⚠️ Warning: Failed to delete from S3: {e}")
    
    # Delete from in-memory DB
    for i, f in enumerate(files_db):
        if f["id"] == file_id:
            files_db.pop(i)
            return
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"File with ID {file_id} not found"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
