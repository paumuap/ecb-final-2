"""MinIO S3 file storage configuration for medical files"""
from minio import Minio
from minio.error import S3Error
import os
from dotenv import load_dotenv
from datetime import timedelta
import uuid
from io import BytesIO

load_dotenv()

# Initialize MinIO client with Play server (public testing)
# Using public credentials: anyone can read world-readable files
# For production, use private MinIO or AWS S3
minio_client = Minio(
    endpoint="play.min.io",
    access_key="Q3AM3UQ867SPQQA43P2F",
    secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    secure=True
)

BUCKET_NAME = "ecb-medical-files"
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.txt', '.fasta', '.fa', '.seq'}


async def init_bucket():
    """Create bucket if it doesn't exist"""
    try:
        exists = minio_client.bucket_exists(BUCKET_NAME)
        if not exists:
            minio_client.make_bucket(BUCKET_NAME)
            print(f"✅ Created bucket: {BUCKET_NAME}")
        else:
            print(f"✅ Bucket exists: {BUCKET_NAME}")
    except S3Error as e:
        print(f"⚠️ Error initializing bucket: {e}")


async def upload_file(file_content: bytes, filename: str, patient_id: int, file_type: str) -> dict:
    """
    Upload file to MinIO and return metadata for database storage
    
    Args:
        file_content: Binary file content
        filename: Original filename
        patient_id: Patient ID for organization
        file_type: Type of file (report, scan, lab_result, etc.)
    
    Returns:
        dict with s3_key, original_filename, file_size, file_type
    """
    try:
        # Generate unique S3 key with patient ID prefix
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {file_ext} not allowed")
        
        unique_id = str(uuid.uuid4())[:8]
        s3_key = f"patient-{patient_id}/{file_type}/{unique_id}-{filename}"
        
        # Wrap bytes in BytesIO for MinIO
        file_stream = BytesIO(file_content)
        
        # Upload to MinIO
        minio_client.put_object(
            BUCKET_NAME,
            s3_key,
            file_stream,
            length=len(file_content),
            metadata={
                "patient-id": str(patient_id),
                "file-type": file_type,
                "original-name": filename
            }
        )
        
        return {
            "s3_key": s3_key,
            "original_filename": filename,
            "file_size": len(file_content),
            "file_type": file_type
        }
    except Exception as e:
        raise ValueError(f"Upload failed: {str(e)}")


async def download_file(s3_key: str) -> bytes:
    """Download file from MinIO"""
    try:
        response = minio_client.get_object(BUCKET_NAME, s3_key)
        return response.read()
    except S3Error as e:
        raise ValueError(f"Download failed: {str(e)}")


def get_presigned_url(s3_key: str, expires_hours: int = 24) -> str:
    """
    Generate presigned URL for downloading file without authentication
    
    Args:
        s3_key: S3 object key
        expires_hours: URL expiration time in hours
    
    Returns:
        Presigned download URL
    """
    try:
        url = minio_client.get_presigned_download_url(
            BUCKET_NAME,
            s3_key,
            expires=timedelta(hours=expires_hours)
        )
        return url
    except S3Error as e:
        raise ValueError(f"Failed to generate presigned URL: {str(e)}")


def delete_file(s3_key: str):
    """Delete file from MinIO"""
    try:
        minio_client.remove_object(BUCKET_NAME, s3_key)
    except S3Error as e:
        raise ValueError(f"Delete failed: {str(e)}")
