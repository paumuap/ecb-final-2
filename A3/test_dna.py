"""Test DNA sequence API and Biopython utilities"""

import requests
import json
from bio_processor import (
    calculate_gc_fraction, reverse_complement, design_primer,
    detect_snps, translate_dna, find_orfs, read_fasta
)

BASE_URL = "http://localhost:8001/api"

def test_bio_utilities():
    """Test Biopython utilities directly"""
    print("🧬 Testing Biopython Utilities\n")
    
    # Test 1: GC Fraction
    print("1️⃣ GC Fraction calculation")
    seq = "ATGATGATGATGATGATGATG"
    gc = calculate_gc_fraction(seq)
    print(f"   Sequence: {seq}")
    print(f"   GC Fraction: {gc:.3f} ({gc*100:.1f}%)\n")
    
    # Test 2: Reverse Complement
    print("2️⃣ Reverse Complement")
    print(f"   Original:   {seq}")
    rc = reverse_complement(seq)
    print(f"   Reverse:    {rc}")
    print(f"   Double RC:  {reverse_complement(rc)} (should equal original)\n")
    
    # Test 3: Primer Design
    print("3️⃣ Primer Design (Wallace's rule)")
    target = "ATGATGATGATGATGATGATGATGATGATG"
    forward, reverse = design_primer(target, primer_length=20)
    print(f"   Target region: {target}")
    print(f"   Forward primer: {forward}")
    print(f"   Reverse primer: {reverse}\n")
    
    # Test 4: SNP Detection
    print("4️⃣ SNP Detection")
    ref = "ATGATGATGATGATGATGATG"
    query = "ATGATGCCGATGATGATGATG"
    mutations = detect_snps(ref, query)
    print(f"   Reference: {ref}")
    print(f"   Query:     {query}")
    print(f"   Mutations found: {len(mutations)}")
    for mut in mutations[:3]:
        print(f"      Position {mut['position']}: {mut['reference']}→{mut['query']}\n")
    
    # Test 5: Translation
    print("5️⃣ DNA to Protein Translation")
    dna_seq = "ATGATGATGATGTAG"
    protein = translate_dna(dna_seq)
    print(f"   DNA:     {dna_seq}")
    print(f"   Protein: {protein}\n")
    
    # Test 6: ORF Finding
    print("6️⃣ Open Reading Frame (ORF) Detection")
    long_seq = "GCGATGATGATGATGATGTAAATGATGATGTAG"
    orfs = find_orfs(long_seq, min_length=9)
    print(f"   Sequence: {long_seq}")
    print(f"   ORFs found: {len(orfs)}")
    for orf in orfs[:2]:
        print(f"      {orf['start']}-{orf['end']}: {orf['protein']}\n")

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints\n")
    
    try:
        # Test 1: Create Gene
        print("1️⃣ Creating gene BRCA1...")
        gene_response = requests.post(
            f"{BASE_URL}/genes",
            json={
                "symbol": "BRCA1",
                "name": "Breast Cancer Type 1 Susceptibility Protein",
                "ncbi_id": "672",
                "chromosome": "17",
                "start_position": 41196312,
                "end_position": 41277500
            }
        )
        if gene_response.status_code == 201:
            gene = gene_response.json()
            gene_id = gene["id"]
            print(f"   ✅ Created gene ID: {gene_id}\n")
        else:
            print(f"   ❌ Failed: {gene_response.text}\n")
            return
        
        # Test 2: Create Sequence
        print("2️⃣ Creating sequence...")
        seq_response = requests.post(
            f"{BASE_URL}/sequences",
            json={
                "gene_id": gene_id,
                "accession": "NM_007294",
                "sequence": "ATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATG",
                "organism": "Homo sapiens",
                "seq_type": "mRNA"
            }
        )
        if seq_response.status_code == 201:
            seq = seq_response.json()
            seq_id = seq["id"]
            print(f"   ✅ Created sequence ID: {seq_id}")
            print(f"   GC Fraction: {seq['gc_fraction']:.3f}\n")
        else:
            print(f"   ❌ Failed: {seq_response.text}\n")
            return
        
        # Test 3: Analyze Sequence
        print("3️⃣ Analyzing sequence...")
        analysis_response = requests.post(f"{BASE_URL}/sequences/{seq_id}/analyze")
        if analysis_response.status_code == 200:
            analysis = analysis_response.json()
            print(f"   ✅ Analysis complete")
            print(f"   Length: {analysis['length']} bp")
            print(f"   GC%: {analysis['gc_percentage']:.1f}%")
            print(f"   Composition: A={analysis['composition']['A']}, T={analysis['composition']['T']}, G={analysis['composition']['G']}, C={analysis['composition']['C']}\n")
        else:
            print(f"   ❌ Failed: {analysis_response.text}\n")
        
        # Test 4: List Genes
        print("4️⃣ Listing genes...")
        genes_response = requests.get(f"{BASE_URL}/genes")
        if genes_response.status_code == 200:
            genes = genes_response.json()
            print(f"   ✅ Found {len(genes)} gene(s)\n")
        else:
            print(f"   ❌ Failed: {genes_response.text}\n")
        
        # Test 5: Design Primers
        print("5️⃣ Designing primers...")
        primer_response = requests.post(
            f"{BASE_URL}/primers/design?sequence_id={seq_id}&target_region_start=10&target_region_end=50"
        )
        if primer_response.status_code == 200:
            primers = primer_response.json()
            print(f"   ✅ Primers designed")
            print(f"   Forward: {primers['forward_primer']}")
            print(f"   Reverse: {primers['reverse_primer']}")
            print(f"   Tm: {primers['tm_value']:.1f}°C")
            print(f"   GC%: {primers['gc_content']:.1f}%\n")
        else:
            print(f"   ❌ Failed: {primer_response.text}\n")
        
        # Test 6: Create second sequence for SNP comparison
        print("6️⃣ Creating second sequence for variant detection...")
        seq2_response = requests.post(
            f"{BASE_URL}/sequences",
            json={
                "gene_id": gene_id,
                "accession": "NM_007294.variant",
                "sequence": "ATGATGATGCCGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATG",
                "organism": "Homo sapiens",
                "seq_type": "mRNA"
            }
        )
        if seq2_response.status_code == 201:
            seq2 = seq2_response.json()
            seq2_id = seq2["id"]
            print(f"   ✅ Created variant sequence ID: {seq2_id}\n")
            
            # Test 7: Detect SNPs
            print("7️⃣ Detecting SNPs/variants...")
            snp_response = requests.post(
                f"{BASE_URL}/variants/detect?reference_seq_id={seq_id}&query_seq_id={seq2_id}"
            )
            if snp_response.status_code == 200:
                snps = snp_response.json()
                print(f"   ✅ SNPs detected: {snps['mutation_count']}")
                print(f"   Divergence: {snps['divergence_percentage']:.2f}%")
                for mut in snps['mutations'][:3]:
                    print(f"      Position {mut['position']}: {mut['reference']}→{mut['query']}")
            else:
                print(f"   ❌ Failed: {snp_response.text}")
        
        print("\n✨ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("   Make sure API server is running: python dna_api.py")

if __name__ == "__main__":
    print("=" * 70)
    print("🧬 DNA SEQUENCE MANAGEMENT API TEST SUITE")
    print("=" * 70 + "\n")
    
    # Test utilities first (no API needed)
    test_bio_utilities()
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n" + "=" * 70)