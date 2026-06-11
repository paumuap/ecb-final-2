# 🚀 DNA API Quick Reference

**Base URL**: `http://localhost:8001/api`  
**Docs**: `http://localhost:8001/api/docs`

---

## 🧬 GENES

### Create Gene
```
POST /genes
Content-Type: application/json

{
  "symbol": "BRCA1",
  "name": "Breast Cancer Type 1 Susceptibility Protein",
  "ncbi_id": "672",
  "chromosome": "17",
  "start_position": 41196312,
  "end_position": 41277500
}

Response: 201 Created
{
  "id": 1,
  "symbol": "BRCA1",
  ...
  "created_at": "2026-06-10T23:43:00"
}
```

### List All Genes
```
GET /genes

Response: 200 OK
[
  {"id": 1, "symbol": "BRCA1", ...},
  {"id": 2, "symbol": "BRCA2", ...}
]
```

### Get Gene by ID
```
GET /genes/{gene_id}

Response: 200 OK
{"id": 1, "symbol": "BRCA1", ...}
```

### Update Gene
```
PUT /genes/{gene_id}
Content-Type: application/json

{
  "symbol": "BRCA1",
  "name": "Updated name",
  ...
}

Response: 200 OK
{updated gene object}
```

### Delete Gene
```
DELETE /genes/{gene_id}

Response: 204 No Content
```

---

## 🧵 SEQUENCES

### Create Sequence
```
POST /sequences
Content-Type: application/json

{
  "gene_id": 1,
  "accession": "NM_007294",
  "sequence": "ATGATGATGATGATGATGATG",
  "organism": "Homo sapiens",
  "seq_type": "mRNA"
}

Response: 201 Created
{
  "id": 1,
  "gene_id": 1,
  "gc_fraction": 0.333,
  "length": 21,
  ...
}
```

### List Sequences
```
GET /sequences?gene_id=1

Response: 200 OK
[
  {"id": 1, "gene_id": 1, ...},
  {"id": 2, "gene_id": 1, ...}
]
```

### Get Sequence by ID
```
GET /sequences/{seq_id}

Response: 200 OK
{"id": 1, "gene_id": 1, "sequence": "ATG...", ...}
```

### Upload FASTA File
```
POST /sequences/upload?gene_id=1
Content-Type: multipart/form-data

file: @sequences.fasta

Response: 201 Created
[
  {"id": 1, "gene_id": 1, ...},
  {"id": 2, "gene_id": 1, ...}
]
```

---

## 🔬 SEQUENCE ANALYSIS

### Analyze Sequence
```
POST /sequences/{seq_id}/analyze

Response: 200 OK
{
  "sequence": "ATGATGATG...",
  "length": 78,
  "gc_fraction": 0.333,
  "gc_percentage": 33.3,
  "reverse_complement": "CATCATCAT...",
  "properties": {
    "a_count": 26,
    "t_count": 26,
    "g_count": 13,
    "c_count": 13,
    "n_count": 0,
    "is_valid": true
  },
  "composition": {
    "A": 26, "T": 26, "G": 13, "C": 13, "N": 0
  }
}
```

---

## 🧪 PRIMER DESIGN

### Design Primers
```
POST /primers/design?sequence_id=1&target_region_start=10&target_region_end=50&primer_length=20

Response: 200 OK
{
  "forward_primer": "ATGATGATGATGATGATGAT",
  "reverse_primer": "CATCATCATCATCATCATCA",
  "length": 20,
  "target_region": "TGATGATGATGATGATGATG",
  "tm_value": 54.0,
  "gc_content": 35.0
}
```

**Query Parameters:**
- `sequence_id` (required): ID of sequence
- `target_region_start` (required): Start position (0-based)
- `target_region_end` (required): End position
- `primer_length` (optional): Default 20, min 15, max 35

---

## 🧬 VARIANT DETECTION

### Detect SNPs
```
POST /variants/detect?reference_seq_id=1&query_seq_id=2

Response: 200 OK
{
  "reference_seq": "ATGATGATGATGATGATGATG...",
  "query_seq": "ATGATGCCGATGATGATGATG...",
  "mutations": [
    {
      "position": 7,
      "reference": "A",
      "query": "C",
      "mutation_type": "A>C",
      "codon_position": 2
    },
    {
      "position": 8,
      "reference": "T",
      "query": "C",
      "mutation_type": "T>C",
      "codon_position": 2
    }
  ],
  "mutation_count": 2,
  "divergence_percentage": 9.52
}
```

---

## 🌐 NCBI INTEGRATION

### Download from NCBI
```
POST /sequences/ncbi-download
Content-Type: application/json

{
  "query": "BRCA1 Homo sapiens",
  "database": "nucleotide",
  "max_results": 5
}

Response: 200 OK
[
  {
    "id": 1,
    "gene_id": null,
    "accession": "NC_000017.11",
    "sequence": "GCACCCCAGG...",
    "organism": "Homo sapiens",
    "seq_type": "genomic",
    "gc_fraction": 0.412,
    "length": 81054,
    "created_at": "2026-06-10T23:43:00"
  }
]
```

---

## 🔑 Query Parameters Summary

### Gene Parameters
- `symbol` (string) - Gene symbol (e.g., BRCA1)
- `ncbi_id` (string) - NCBI gene ID
- `chromosome` (string) - Chromosome location
- `start_position` (int) - Start base pair
- `end_position` (int) - End base pair

### Sequence Parameters
- `gene_id` (int) - Reference to gene
- `accession` (string) - GenBank accession
- `sequence` (string) - DNA/RNA/protein sequence
- `organism` (string) - Species name
- `seq_type` (string) - Type: "mRNA", "genomic", "protein"

### Analysis Parameters
- `sequence_id` (int) - Sequence to analyze
- `target_region_start` (int) - Region start (0-based)
- `target_region_end` (int) - Region end
- `primer_length` (int) - Desired primer length (default 20)

### Variant Parameters
- `reference_seq_id` (int) - Reference sequence
- `query_seq_id` (int) - Query sequence to compare

### NCBI Parameters
- `query` (string) - Search query
- `database` (string) - "nucleotide" or "protein"
- `max_results` (int) - Max results to return

---

## 📊 Sequence Types

- `genomic` - Genomic DNA
- `mRNA` - Messenger RNA
- `protein` - Protein sequence
- `rRNA` - Ribosomal RNA
- `tRNA` - Transfer RNA

---

## 🧮 Calculations

### Wallace's Rule for Tm (Melting Temperature)
```
For primers ≤ 13 bp:
Tm = 4(G+C) + 2(A+T)

For primers > 13 bp:
Tm = 64.9 + (41 × (GC%-16.4) / length)

Units: °C
```

### GC Content
```
GC% = (G + C) / length × 100
```

### Divergence
```
Divergence% = (mutations / length) × 100
```

---

## ✅ Response Status Codes

- `200 OK` - Success (GET, POST with no body change)
- `201 Created` - Resource created
- `204 No Content` - Successful deletion
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## 🚨 Common Errors

### "Sequence not found"
```json
{
  "detail": "Sequence with ID 999 not found"
}
```
→ Check if sequence ID exists with `GET /sequences`

### "Invalid sequence"
```json
{
  "detail": "Sequence contains invalid characters. Only ATGCN allowed."
}
```
→ Use only A, T, G, C, N characters

### "Target region out of bounds"
```json
{
  "detail": "Target region end (100) exceeds sequence length (78)"
}
```
→ Ensure target_region_end < sequence length

---

## 💡 Tips & Tricks

1. **Get all sequences for a gene:**
   ```
   GET /sequences?gene_id=1
   ```

2. **Design primers for entire sequence:**
   ```
   POST /primers/design?sequence_id=1&target_region_start=0&target_region_end=100
   ```

3. **Analyze downloaded NCBI sequences:**
   - Download with `/sequences/ncbi-download`
   - Analyze with `/sequences/{id}/analyze`
   - Design primers with `/primers/design`

4. **Compare sequences:**
   - Create two sequences
   - Use `/variants/detect` to find SNPs

5. **Upload multiple sequences:**
   - Create FASTA file with multiple entries
   - POST to `/sequences/upload?gene_id=1`

---

## 🔗 Related Endpoints

```
Workflow 1: Create & Analyze
1. POST /genes                    → Create gene
2. POST /sequences                → Create sequence
3. POST /sequences/{id}/analyze   → Analyze

Workflow 2: Design Primers
1. POST /sequences/upload         → Upload FASTA
2. POST /primers/design           → Design primers

Workflow 3: Compare Sequences
1. POST /sequences                → Create ref sequence
2. POST /sequences                → Create query sequence
3. POST /variants/detect          → Detect SNPs

Workflow 4: Download & Analyze
1. POST /sequences/ncbi-download  → Download
2. POST /sequences/{id}/analyze   → Analyze
3. POST /primers/design           → Design primers
```

---

## 📞 Example Workflows

### Create Gene & Sequence, Then Analyze
```bash
# 1. Create gene
curl -X POST http://localhost:8001/api/genes \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BRCA1","name":"BRCA1 Gene","ncbi_id":"672","chromosome":"17","start_position":41196312,"end_position":41277500}'

# 2. Create sequence (use gene_id from response)
curl -X POST http://localhost:8001/api/sequences \
  -H "Content-Type: application/json" \
  -d '{"gene_id":1,"accession":"NM_007294","sequence":"ATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATG","organism":"Homo sapiens","seq_type":"mRNA"}'

# 3. Analyze (use seq_id from response)
curl -X POST http://localhost:8001/api/sequences/1/analyze

# 4. Design primers
curl -X POST "http://localhost:8001/api/primers/design?sequence_id=1&target_region_start=10&target_region_end=50"
```

---

**API Version**: 1.0.0  
**Last Updated**: June 10, 2026  
**Status**: Production Ready ✅
