"""Test DNA sequence file upload (FASTA and GenBank)"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8001/api"

def test_file_uploads():
    """Test FASTA and GenBank file uploads"""
    print("=" * 70)
    print("🧬 DNA SEQUENCE FILE UPLOAD TEST")
    print("=" * 70 + "\n")
    
    try:
        # Step 1: Create a gene
        print("1️⃣ Creating gene record for uploads...")
        gene_response = requests.post(
            f"{BASE_URL}/genes",
            json={
                "symbol": "TEST_GENE",
                "name": "Test Gene for File Uploads",
                "ncbi_id": "12345",
                "chromosome": "1",
                "start_position": 100000,
                "end_position": 200000
            }
        )
        if gene_response.status_code != 201:
            print(f"❌ Gene creation failed: {gene_response.text}")
            return
        
        gene = gene_response.json()
        gene_id = gene["id"]
        print(f"✅ Gene created with ID: {gene_id}\n")
        
        # Step 2: Upload FASTA file
        print("2️⃣ Testing FASTA file upload...")
        fasta_file_path = Path(__file__).parent / "test_sample.fasta"
        
        if not fasta_file_path.exists():
            print(f"⚠️ FASTA test file not found: {fasta_file_path}")
        else:
            with open(fasta_file_path, 'rb') as f:
                files = {'file': f}
                fasta_response = requests.post(
                    f"{BASE_URL}/sequences/upload-fasta?gene_id={gene_id}",
                    files=files
                )
            
            if fasta_response.status_code == 201:
                sequences = fasta_response.json()
                print(f"✅ FASTA upload successful!")
                print(f"   Sequences imported: {len(sequences)}")
                for seq in sequences:
                    print(f"      - {seq['accession']}: {seq['length']} bp (GC: {seq['gc_fraction']*100:.1f}%)")
                print()
            else:
                print(f"❌ FASTA upload failed: {fasta_response.text}\n")
        
        # Step 3: Upload GenBank file
        print("3️⃣ Testing GenBank file upload...")
        genbank_file_path = Path(__file__).parent / "test_sample.gb"
        
        if not genbank_file_path.exists():
            print(f"⚠️ GenBank test file not found: {genbank_file_path}")
        else:
            with open(genbank_file_path, 'rb') as f:
                files = {'file': f}
                genbank_response = requests.post(
                    f"{BASE_URL}/sequences/upload-genbank?gene_id={gene_id}",
                    files=files
                )
            
            if genbank_response.status_code == 201:
                sequences = genbank_response.json()
                print(f"✅ GenBank upload successful!")
                print(f"   Sequences imported: {len(sequences)}")
                for seq in sequences:
                    print(f"      - {seq['accession']}: {seq['length']} bp (GC: {seq['gc_fraction']*100:.1f}%)")
                print()
            else:
                print(f"❌ GenBank upload failed: {genbank_response.text}\n")
        
        # Step 4: Test generic upload endpoint (auto-detect format)
        print("4️⃣ Testing generic upload endpoint (auto-detect)...")
        with open(fasta_file_path, 'rb') as f:
            files = {'file': f}
            generic_response = requests.post(
                f"{BASE_URL}/sequences/upload?gene_id={gene_id}",
                files=files
            )
        
        if generic_response.status_code == 201:
            sequences = generic_response.json()
            print(f"✅ Generic upload successful (auto-detected FASTA)")
            print(f"   Sequences imported: {len(sequences)}\n")
        else:
            print(f"❌ Generic upload failed: {generic_response.text}\n")
        
        # Step 5: List all sequences for this gene
        print("5️⃣ Listing all sequences for gene...")
        list_response = requests.get(f"{BASE_URL}/sequences?gene_id={gene_id}")
        if list_response.status_code == 200:
            all_sequences = list_response.json()
            print(f"✅ Total sequences: {len(all_sequences)}")
            for seq in all_sequences[:5]:
                print(f"   - ID {seq['id']}: {seq['accession']} ({seq['length']} bp)")
            print()
        else:
            print(f"❌ Listing failed: {list_response.text}\n")
        
        # Step 6: Analyze first sequence
        if all_sequences:
            print("6️⃣ Analyzing first sequence...")
            seq_id = all_sequences[0]['id']
            analysis_response = requests.post(f"{BASE_URL}/sequences/{seq_id}/analyze")
            
            if analysis_response.status_code == 200:
                analysis = analysis_response.json()
                print(f"✅ Analysis complete:")
                print(f"   Length: {analysis['length']} bp")
                print(f"   GC%: {analysis['gc_percentage']:.1f}%")
                print(f"   Composition: A={analysis['composition']['A']}, T={analysis['composition']['T']}, G={analysis['composition']['G']}, C={analysis['composition']['C']}\n")
            else:
                print(f"❌ Analysis failed: {analysis_response.text}\n")
        
        print("✨ File upload tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("   Make sure API server is running: python dna_api.py")

if __name__ == "__main__":
    test_file_uploads()
