## NCBI Sequence Download & Persistence Integration

This document describes the NCBI Entrez integration for downloading DNA sequences and persisting them to the database with Tortoise ORM.

### Features

✅ **NCBI Entrez Integration**
- Search nucleotide and protein databases
- Download sequences by gene name, accession, or query
- Automatic GC content calculation
- Support for up to 20 results per query

✅ **Database Persistence**
- Tortoise ORM models for Gene and Sequence storage
- Automatic gene creation if not exists
- Sequence metadata storage (accession, organism, GC fraction, etc.)
- Audit trail with created_at/updated_at timestamps

✅ **User Interface**
- 3-step downloader workflow:
  1. Search NCBI by gene name or accession
  2. Select sequences from results
  3. Save to database with gene association

### Architecture

#### Backend (A3)

**Models** (`models.py`):
- `Gene`: Stores gene information (symbol, name, NCBI ID, chromosome location)
- `Sequence`: Stores DNA/RNA sequences (accession, sequence, organism, GC content)
- `SequenceAnalysis`: Stores primer design and analysis results

**Database** (`database.py`):
- Tortoise ORM initialization (SQLite for development)
- Automatic schema generation

**API Endpoints** (`dna_api.py`):

1. **Search NCBI** (existing)
   ```
   POST /api/sequences/ncbi-download
   
   Request:
   {
     "query": "BRCA1 human mRNA",
     "database": "nucleotide",
     "max_results": 5
   }
   ```

2. **Search and Save to Database** (new)
   ```
   POST /api/genes/{gene_symbol}/sequences/ncbi-search
   
   Request:
   {
     "query": "BRCA1 mRNA",
     "database": "nucleotide",
     "max_results": 5
   }
   ```

3. **Save Individual Sequence** (new)
   ```
   POST /api/sequences/ncbi-download-and-save
   
   Request:
   {
     "gene_symbol": "BRCA1",
     "gene_name": "Breast Cancer Type 1 Susceptibility Protein",
     "ncbi_accession": "NM_007294.4",
     "sequence": "ATCGATCG...",
     "organism": "Homo sapiens",
     "description": "mRNA for BRCA1"
   }
   ```

#### Frontend (A2)

**Component** (`NCBIDownloader.tsx`):
- Search interface with database selection
- Results display with organism, length, GC content
- Multi-select for sequences
- Gene symbol and name input
- Save to database with visual feedback

### Usage Workflow

#### 1. Search NCBI

Enter a search query:
- Gene name: `BRCA1 human mRNA`
- Accession: `NM_007294`
- Description: `TP53 tumor suppressor`

Select database:
- **Nucleotide**: DNA/RNA sequences
- **Protein**: Amino acid sequences

Set max results (1-20, default 5)

#### 2. Select Sequences

Click checkboxes to select which sequences to save.
View:
- NCBI accession number
- Description from NCBI
- Organism
- Sequence length
- GC content percentage

#### 3. Associate with Gene

Enter gene symbol (required):
- Will be created if it doesn't exist
- Example: `BRCA1`, `TP53`, `MYH7`

Enter gene name (optional):
- Full gene description
- Example: "Breast Cancer Type 1 Susceptibility Protein"

#### 4. Save to Database

Click "Save Sequences" to:
1. Create gene record if needed
2. Save each selected sequence
3. Calculate GC fraction
4. Store metadata (organism, accession, description)

### Example Queries

**By Gene Name**:
```
BRCA1 human mRNA
TP53 Homo sapiens
MYH7 heart protein
```

**By Accession**:
```
NM_007294       (BRCA1 mRNA)
NP_009225       (BRCA1 protein)
NM_000546       (TP53 mRNA)
```

**By Description**:
```
BRCA1 mRNA human
tumor suppressor protein 53
myosin heavy chain 7
```

### Database Schema

#### genes table
| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| symbol | varchar(50) | Gene symbol (BRCA1, TP53, etc.) |
| name | varchar(255) | Full gene name |
| ncbi_id | varchar(50) | NCBI gene ID |
| chromosome | varchar(10) | Chromosome location |
| start_position | bigint | Start position on chromosome |
| end_position | bigint | End position on chromosome |
| description | text | Gene description |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

#### sequences table
| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| gene_id | int | Foreign key to genes table |
| accession | varchar(50) | NCBI accession (NM_007294, NP_009225) |
| sequence | text | DNA/RNA/protein sequence |
| description | text | Description from NCBI |
| organism | varchar(255) | Organism name (Homo sapiens) |
| seq_type | varchar(20) | genomic, mRNA, protein |
| gc_fraction | float | GC content as fraction (0.0-1.0) |
| gc_percentage | float | GC content as percentage (0-100) |
| length | int | Sequence length in bases |
| source | varchar(50) | Source: ncbi, upload, computed |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

#### sequence_analyses table
| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| sequence_id | int | Foreign key to sequences table |
| analysis_type | varchar(50) | primer_design, snp_detection, gc_analysis |
| parameters | json | Analysis parameters |
| results | json | Analysis results |
| created_at | datetime | Creation timestamp |

### API Response Examples

**Search Results**:
```json
{
  "query": "BRCA1 human mRNA",
  "count": 5,
  "sequences": [
    {
      "accession": "NM_007294.4",
      "description": "Homo sapiens BRCA1 DNA repair associated (BRCA1), mRNA",
      "organism": "Homo sapiens",
      "sequence": "ATGGATTATTC...TGATTATAA",
      "length": 7280,
      "gc_fraction": 0.42
    },
    ...
  ]
}
```

**Save Success**:
```json
{
  "gene_id": 5,
  "sequence_id": 42,
  "message": "Sequence NM_007294.4 saved for gene BRCA1"
}
```

### Requirements

**Python Packages**:
```
biopython>=1.87       # Entrez and sequence parsing
tortoise-orm>=0.21.0  # ORM for database
aiosqlite>=3.1.0      # Async SQLite driver
```

**NCBI Configuration**:
- Entrez.email is set to "bioinformatics@ecb.local"
- Rate limiting: 3 requests per second (NCBI requirement)

### Integration with A2

The saved sequences are available to:
1. **PatientDetails**: Display patient's associated sequences
2. **PrimerDesigner**: Design primers for saved sequences
3. **VariantDetector**: Detect variants in saved sequences
4. **SequenceAnalysis**: Analyze composition and properties

### Future Enhancements

- [ ] Batch import from GenBank files
- [ ] Sequence alignment and comparison
- [ ] Variant calling pipeline
- [ ] FASTA/GenBank export
- [ ] Sequence visualization
- [ ] Multiple sequence alignment

### Troubleshooting

**NCBI Connection Errors**:
- Check internet connectivity
- Verify Entrez.email is set
- Rate limiting: wait 1 second between requests

**Database Errors**:
- Ensure tortoise-orm is installed: `pip install tortoise-orm aiosqlite`
- Check database file permissions
- Verify models.py is in correct location

**Duplicate Sequences**:
- Accession numbers are unique in the database
- Duplicate accessions are skipped during import

### References

- [NCBI Entrez Documentation](https://www.ncbi.nlm.nih.gov/books/NBK179288/)
- [Biopython Tutorial](https://biopython.org/wiki/Documentation)
- [Tortoise ORM Documentation](https://tortoise-orm.readthedocs.io/)
