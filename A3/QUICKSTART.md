# 🚀 DNA API Quick Start

Get the DNA sequence management API running in 5 minutes.

## Step 1: Install Dependencies

```bash
cd C:\code\ecb-final\A3
pip install -r requirements.txt
```

This installs:
- `fastapi` - Web framework
- `uvicorn` - ASGI server  
- `biopython` - Bioinformatics library
- `requests` - HTTP client

## Step 2: Start the API Server

```bash
python dna_api.py
```

Or with explicit port:
```bash
uvicorn dna_api:app --reload --port 8001
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

## Step 3: Verify API is Running

Visit in browser:
- **API Documentation**: http://localhost:8001/api/docs
- **ReDoc Alternative**: http://localhost:8001/api/redoc

Both show all 13 endpoints with live testing.

## Step 4: Run Tests

In a new terminal (keep API running):

```bash
cd C:\code\ecb-final\A3
python test_dna.py
```

This runs:
1. **Biopython utilities test** (no API needed)
   - GC fraction
   - Reverse complement
   - Primer design
   - SNP detection
   - Translation
   - ORF finding

2. **API endpoint tests** (requires running API)
   - Create gene
   - Create sequence
   - Analyze sequence
   - Design primers
   - Detect SNPs

Expected output:
```
🧬 Testing Biopython Utilities

1️⃣ GC Fraction calculation
   Sequence: ATGATGATGATGATGATGATG
   GC Fraction: 0.333 (33.3%)

...

🌐 Testing API Endpoints

1️⃣ Creating gene BRCA1...
   ✅ Created gene ID: 1

...

✨ All tests completed!
```

## Step 5: Try Some Examples

### Create a Gene
```bash
curl -X POST http://localhost:8001/api/genes \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BRCA1",
    "name": "Breast Cancer Type 1 Susceptibility Protein",
    "ncbi_id": "672",
    "chromosome": "17",
    "start_position": 41196312,
    "end_position": 41277500
  }'
```

### Create a Sequence
```bash
curl -X POST http://localhost:8001/api/sequences \
  -H "Content-Type: application/json" \
  -d '{
    "gene_id": 1,
    "accession": "NM_007294",
    "sequence": "ATGATGATGATGATGATGATG",
    "organism": "Homo sapiens",
    "seq_type": "mRNA"
  }'
```

### Analyze Sequence
```bash
curl -X POST http://localhost:8001/api/sequences/1/analyze
```

### Design Primers
```bash
curl -X POST "http://localhost:8001/api/primers/design?sequence_id=1&target_region_start=0&target_region_end=100"
```

## API Structure

```
API Root: /api

├── Genes (5 endpoints)
│  ├── POST   /genes              (create)
│  ├── GET    /genes              (list all)
│  ├── GET    /genes/{id}         (get one)
│  ├── PUT    /genes/{id}         (update)
│  └── DELETE /genes/{id}         (delete)
│
├── Sequences (4 endpoints)
│  ├── POST   /sequences          (create)
│  ├── GET    /sequences          (list with filters)
│  ├── GET    /sequences/{id}     (get one)
│  └── POST   /sequences/upload   (upload FASTA)
│
├── Sequence Analysis (4 endpoints)
│  ├── POST   /sequences/{id}/analyze   (full analysis)
│  ├── POST   /primers/design           (primer design)
│  ├── POST   /variants/detect          (SNP detection)
│  └── POST   /sequences/ncbi-download  (NCBI download)
```

## What Each Module Does

### `dna_api.py` (Main API Server)
- FastAPI application
- 13 REST endpoints
- Pydantic models for validation
- In-memory storage (ready for Tortoise ORM)

### `bio_processor.py` (Biopython Wrapper)
- File I/O: FASTA, GenBank parsing
- Sequence analysis: GC%, reverse complement, composition
- Primer design: Wallace's rule melting temperature
- Variant detection: SNP calling
- NCBI integration: Entrez downloads
- Translation: DNA→Protein with genetic code

### `requirements.txt`
- Python package dependencies

### `test_dna.py`
- Unit tests for utilities
- Integration tests for API endpoints
- Example usage patterns

## Troubleshooting

### "ModuleNotFoundError: No module named 'Bio'"
```bash
pip install biopython
```

### API won't start
Check if port 8001 is in use:
```powershell
Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
```

If occupied, use different port:
```bash
uvicorn dna_api:app --reload --port 8002
```

### Tests fail with "Connection refused"
Make sure API is running in another terminal:
```bash
python dna_api.py
```

### NCBI download fails
- Check internet connection
- Verify email is set (Entrez requires it)
- NCBI has rate limits (~3 requests/second)

## Next Steps

1. **Expand frontend** (React/Vite in ecb-2601)
   - Sequence upload form
   - Primer design calculator
   - Variant viewer
   - NCBI search widget

2. **Add database** (PostgreSQL + Tortoise ORM)
   - Persistent storage
   - User authentication
   - Role-based access

3. **Production deployment**
   - Docker containerization
   - Gunicorn ASGI server
   - Nginx reverse proxy

## File Upload Example

To upload a FASTA file:

```bash
# First, create a test FASTA file
@(
'> seq1 Homo sapiens'
'ATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATG'
'> seq2 variant'
'ATGATGATGCCGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATGATG'
) | Add-Content -Path test.fasta

# Upload it
curl -X POST "http://localhost:8001/api/sequences/upload?gene_id=1" `
  -F "file=@test.fasta"
```

## API Response Examples

### Successful Gene Creation
```json
{
  "id": 1,
  "symbol": "BRCA1",
  "name": "Breast Cancer Type 1 Susceptibility Protein",
  "ncbi_id": "672",
  "chromosome": "17",
  "start_position": 41196312,
  "end_position": 41277500,
  "created_at": "2026-06-10T23:43:00"
}
```

### Sequence Analysis
```json
{
  "sequence": "ATGATGATGATGATGATGATG...",
  "length": 81,
  "gc_fraction": 0.395,
  "gc_percentage": 39.5,
  "reverse_complement": "CATCATCATCATCATCATCAT...",
  "properties": {
    "a_count": 25,
    "t_count": 25,
    "g_count": 15,
    "c_count": 16,
    "n_count": 0
  },
  "composition": {
    "A": 25,
    "T": 25,
    "G": 15,
    "C": 16,
    "N": 0
  }
}
```

### Primer Design
```json
{
  "forward_primer": "ATGATGATGATGATGATGATG",
  "reverse_primer": "CATCATCATCATCATCATCAT",
  "length": 20,
  "tm_value": 68.0,
  "gc_content": 50.0
}
```

---

**Ready to go!** 🚀

Questions? Check `DNA_API_README.md` for full documentation.
