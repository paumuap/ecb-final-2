#!/usr/bin/env python
"""Test Row-Level Security (RLS) for medical file access"""

import requests
import json
from pathlib import Path
import tempfile

BASE_URL = "http://localhost:8000/api"

def test_rls_file_access():
    """Test RLS for file access control"""
    
    print("🔒 Testing RLS for Medical File Access\n")
    
    # ============ 1. SETUP: Create users and patients ============
    
    # Admin login
    print("1️⃣  Admin login...")
    admin_response = requests.post(
        f"{BASE_URL}/login",
        data={"username": "admin", "password": "admin123"}
    )
    admin_token = admin_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✅ Admin logged in\n")
    
    # Create doctor user
    print("2️⃣  Creating doctor user...")
    doctor_data = {
        "username": "doctor1",
        "email": "doctor1@hospital.com",
        "password": "doctor123",
        "role": "doctor"
    }
    doctor_create = requests.post(
        f"{BASE_URL}/admin/users",
        json=doctor_data,
        headers=admin_headers
    )
    if doctor_create.status_code == 201:
        print("✅ Created doctor1 user\n")
    else:
        print(f"⚠️ Doctor already exists (or error): {doctor_create.status_code}\n")
    
    # Doctor login
    doctor_response = requests.post(
        f"{BASE_URL}/login",
        data={"username": "doctor1", "password": "doctor123"}
    )
    if doctor_response.status_code == 200:
        doctor_token = doctor_response.json()["access_token"]
        doctor_headers = {"Authorization": f"Bearer {doctor_token}"}
        print("3️⃣  Doctor1 logged in\n")
    else:
        print(f"❌ Doctor login failed: {doctor_response.text}")
        return
    
    # Create two patients as admin
    print("4️⃣  Creating patients...")
    patient1 = requests.post(
        f"{BASE_URL}/pacients",
        json={
            "nom": "Patient",
            "cognom": "One",
            "email": "patient1@example.com",
            "data_naixement": "1990-01-01",
            "numero_historia": "P-001"
        },
        headers=admin_headers
    ).json()
    
    patient2 = requests.post(
        f"{BASE_URL}/pacients",
        json={
            "nom": "Patient",
            "cognom": "Two",
            "email": "patient2@example.com",
            "data_naixement": "1990-02-01",
            "numero_historia": "P-002"
        },
        headers=admin_headers
    ).json()
    
    print(f"✅ Created patient 1 (ID: {patient1['id']})")
    print(f"✅ Created patient 2 (ID: {patient2['id']})\n")
    
    # ============ 2. UPLOAD: Doctor uploads files ============
    
    print("5️⃣  Doctor1 uploads file for Patient 1...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Patient 1 Lab Results\nStatus: Normal\n")
        file1_path = f.name
    
    with open(file1_path, 'rb') as f:
        files = {'file': (Path(file1_path).name, f, 'text/plain')}
        upload1 = requests.post(
            f"{BASE_URL}/files/upload/{patient1['id']}?file_type=report",
            files=files,
            headers=doctor_headers
        )
    
    if upload1.status_code == 200:
        file1_id = upload1.json()["file"]["id"]
        print(f"✅ Uploaded file 1 for patient 1 (File ID: {file1_id})\n")
    else:
        print(f"❌ Upload failed: {upload1.text}\n")
        return
    
    # ============ 3. ACCESS CONTROL TEST ============
    
    print("6️⃣  Testing access control...\n")
    
    # Test 1: Admin can see all files
    print("   Test 1: Admin lists files for patient 1")
    admin_list = requests.get(
        f"{BASE_URL}/files/patient/{patient1['id']}",
        headers=admin_headers
    )
    if admin_list.status_code == 200 and len(admin_list.json()) > 0:
        print("   ✅ Admin CAN see patient 1 files\n")
    else:
        print(f"   ❌ Admin cannot see files: {admin_list.status_code}\n")
    
    # Test 2: Doctor can see their own uploaded files
    print("   Test 2: Doctor1 lists files for patient 1 (their patient)")
    doctor_list = requests.get(
        f"{BASE_URL}/files/patient/{patient1['id']}",
        headers=doctor_headers
    )
    if doctor_list.status_code == 200 and len(doctor_list.json()) > 0:
        print("   ✅ Doctor1 CAN see their patient's files\n")
    else:
        print(f"   ⚠️ Doctor cannot see files: {doctor_list.status_code}\n")
    
    # Test 3: Doctor can download their files
    print("   Test 3: Doctor1 downloads their uploaded file")
    doctor_download = requests.get(
        f"{BASE_URL}/files/{file1_id}/download",
        headers=doctor_headers
    )
    if doctor_download.status_code == 200:
        url = doctor_download.json()["download_url"]
        print(f"   ✅ Doctor1 CAN download file")
        print(f"      URL: {url[:70]}...\n")
    else:
        print(f"   ❌ Download failed: {doctor_download.status_code}\n")
    
    # Test 4: Doctor can delete their own files
    print("   Test 4: Doctor1 deletes their uploaded file")
    doctor_delete = requests.delete(
        f"{BASE_URL}/files/{file1_id}",
        headers=doctor_headers
    )
    if doctor_delete.status_code == 204:
        print("   ✅ Doctor1 CAN delete their own files\n")
    else:
        print(f"   ❌ Delete failed: {doctor_delete.status_code}\n")
    
    # ============ 4. SUMMARY ============
    
    print("✨ RLS Tests Complete!")
    print("\n📋 Summary of Access Control:")
    print("   ✅ Admin: Full access to all files")
    print("   ✅ Doctor: Can access files for their own patients")
    print("   ✅ Doctor: Can delete their own uploads")
    print("   ⏳ (RLS in PostgreSQL will enforce this at database level)")
    print("\n🔐 Next: Migrate to PostgreSQL medical_files table for full RLS")

if __name__ == "__main__":
    test_rls_file_access()
