#!/usr/bin/env python
"""Test MinIO file storage integration with ECB API"""

import requests
import json
from pathlib import Path
import tempfile

BASE_URL = "http://localhost:8000/api"

def test_file_storage():
    """Test complete file upload workflow"""
    
    print("🧪 Testing ECB File Storage Integration\n")
    
    # 1. Login
    print("1️⃣  Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/login",
        data={"username": "admin", "password": "admin123"}
    )
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ Logged in as admin")
    print(f"   Token: {token[:20]}...\n")
    
    # 2. Create a patient
    print("2️⃣  Creating a test patient...")
    patient_data = {
        "nom": "Test",
        "cognom": "Patient",
        "email": "patient@example.com",
        "data_naixement": "1990-01-15",
        "numero_historia": "TEST-001"
    }
    patient_response = requests.post(
        f"{BASE_URL}/pacients",
        json=patient_data,
        headers=headers
    )
    if patient_response.status_code != 201:
        print(f"❌ Patient creation failed: {patient_response.text}")
        return
    
    patient = patient_response.json()
    patient_id = patient["id"]
    print(f"✅ Created patient ID: {patient_id}\n")
    
    # 3. Create a test file
    print("3️⃣  Creating test medical file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test Lab Results\n")
        f.write("Date: 2026-06-10\n")
        f.write("Status: Normal\n")
        test_file_path = f.name
    
    print(f"✅ Created test file: {test_file_path}\n")
    
    # 4. Upload file to MinIO
    print("4️⃣  Uploading file to MinIO...")
    with open(test_file_path, 'rb') as f:
        files = {'file': (Path(test_file_path).name, f, 'text/plain')}
        upload_response = requests.post(
            f"{BASE_URL}/files/upload/{patient_id}?file_type=report",
            files=files,
            headers=headers
        )
    
    if upload_response.status_code != 200:
        print(f"❌ Upload failed: {upload_response.text}")
        return
    
    upload_result = upload_response.json()
    file_id = upload_result["file"]["id"]
    s3_key = upload_result["file"]["s3_key"]
    
    print(f"✅ File uploaded successfully!")
    print(f"   File ID: {file_id}")
    print(f"   S3 Key: {s3_key}")
    print(f"   Size: {upload_result['file']['file_size']} bytes\n")
    
    # 5. List patient files
    print("5️⃣  Listing patient files...")
    list_response = requests.get(
        f"{BASE_URL}/files/patient/{patient_id}",
        headers=headers
    )
    
    if list_response.status_code != 200:
        print(f"❌ List failed: {list_response.text}")
        return
    
    files_list = list_response.json()
    print(f"✅ Found {len(files_list)} file(s) for patient {patient_id}:")
    for file_info in files_list:
        print(f"   - {file_info['original_filename']} ({file_info['file_type']}) - {file_info['file_size']} bytes")
    print()
    
    # 6. Get download URL
    print("6️⃣  Generating presigned download URL...")
    download_response = requests.get(
        f"{BASE_URL}/files/{file_id}/download",
        headers=headers
    )
    
    if download_response.status_code != 200:
        print(f"❌ Download URL generation failed: {download_response.text}")
        return
    
    download_info = download_response.json()
    print(f"✅ Presigned URL generated!")
    print(f"   URL: {download_info['download_url']}")
    print(f"   Valid for: {download_info['expires_in_hours']} hours\n")
    
    # 7. Delete file
    print("7️⃣  Deleting file...")
    delete_response = requests.delete(
        f"{BASE_URL}/files/{file_id}",
        headers=headers
    )
    
    if delete_response.status_code != 204:
        print(f"❌ Delete failed: {delete_response.text}")
        return
    
    print(f"✅ File deleted successfully!\n")
    
    # Cleanup
    Path(test_file_path).unlink()
    
    print("✨ All tests passed!")
    print("\n📋 Summary:")
    print(f"   - Created patient: ID {patient_id}")
    print(f"   - Uploaded file to MinIO: {s3_key}")
    print(f"   - Generated presigned URL")
    print(f"   - Deleted file")
    print("\n🎉 MinIO S3 file storage integration is working!")

if __name__ == "__main__":
    test_file_storage()
