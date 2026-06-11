"""DNA Sequence Management and Processing Module

Features:
- FASTA/GenBank file ingestion with Biopython
- NCBI Entrez integration for sequence download
- Primer design utility (Wallace's rule for Tm)
- SNP/variant detection
- GC fraction and sequence analysis
- Tortoise ORM integration
"""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bio_processor import (
    read_fasta, read_genbank, get_sequence_properties,
    reverse_complement, calculate_gc_fraction, design_primer,
    detect_snps, download_from_ncbi
)
import uvicorn

app = FastAPI(title="ECB DNA Sequence API", version="1.0.0", docs_url="/api/docs")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Models ==============

class GeneModel(BaseModel):
    id: Optional[int] = None
    symbol: str = Field(..., min_length=1, description="Gene symbol (e.g., BRCA1)")
    name: str = Field(..., min_length=1, description="Full gene name")
    ncbi_id: Optional[str] = None
    chromosome: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    created_at: Optional[datetime] = None

class SequenceModel(BaseModel):
    id: Optional[int] = None
    gene_id: int = Field(..., description="Reference to Gene")
    accession: str = Field(..., min_length=1, description="Sequence accession (e.g., NM_007294)")
    sequence: str = Field(..., min_length=1, description="DNA sequence")
    description: Optional[str] = None
    organism: Optional[str] = None
    seq_type: str = Field(default="genomic", description="genomic, mRNA, protein")
    gc_fraction: Optional[float] = None
    length: Optional[int] = None
    created_at: Optional[datetime] = None

class SequenceAnalysisResponse(BaseModel):
    sequence: str
    length: int
    gc_fraction: float
    gc_percentage: float
    reverse_complement: str
    properties: dict
    composition: dict

class PrimerModel(BaseModel):
    forward_primer: str
    reverse_primer: str
    length: int = Field(default=20, description="Primer length")
    target_region: str
    tm_value: float
    gc_content: float

class SNPDetectionResponse(BaseModel):
    reference_seq: str
    query_seq: str
    mutations: List[dict]
    mutation_count: int
    divergence_percentage: float

class NCBIDownloadRequest(BaseModel):
    query: str = Field(..., description="NCBI query string or accession number")
    database: str = Field(default="nucleotide", description="NCBI database")
    max_results: int = Field(default=5)

class SequenceAnalysisRequest(BaseModel):
    sequence: str = Field(..., description="Raw DNA sequence to analyze")

# ============== In-Memory Storage ==============

genes_db = []
sequences_db = []
gene_id_counter = 1
sequence_id_counter = 1

# ============== Endpoints ==============

# --- GENES ---

@app.post("/api/genes", response_model=GeneModel, status_code=status.HTTP_201_CREATED)
async def create_gene(gene: GeneModel):
    """Create a new gene record"""
    global gene_id_counter
    gene_data = gene.dict()
    gene_data["id"] = gene_id_counter
    gene_data["created_at"] = datetime.utcnow()
    genes_db.append(gene_data)
    gene_id_counter += 1
    return gene_data

@app.get("/api/genes", response_model=List[GeneModel])
async def list_genes():
    """List all genes"""
    if not genes_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No genes registered"
        )
    return genes_db

@app.get("/api/genes/{gene_id}", response_model=GeneModel)
async def get_gene(gene_id: int):
    """Get gene by ID"""
    gene = next((g for g in genes_db if g["id"] == gene_id), None)
    if not gene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gene with ID {gene_id} not found"
        )
    return gene

@app.put("/api/genes/{gene_id}", response_model=GeneModel)
async def update_gene(gene_id: int, gene_update: GeneModel):
    """Update gene information"""
    for i, g in enumerate(genes_db):
        if g["id"] == gene_id:
            updated = gene_update.dict()
            updated["id"] = gene_id
            updated["created_at"] = g["created_at"]
            genes_db[i] = updated
            return updated
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Gene with ID {gene_id} not found"
    )

@app.delete("/api/genes/{gene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gene(gene_id: int):
    """Delete a gene"""
    for i, g in enumerate(genes_db):
        if g["id"] == gene_id:
            genes_db.pop(i)
            return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Gene with ID {gene_id} not found"
    )

# --- SEQUENCES ---

@app.post("/api/sequences", response_model=SequenceModel, status_code=status.HTTP_201_CREATED)
async def create_sequence(sequence: SequenceModel):
    """Create a new sequence record"""
    global sequence_id_counter
    
    # Verify gene exists
    if not any(g["id"] == sequence.gene_id for g in genes_db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gene with ID {sequence.gene_id} not found"
        )
    
    seq_data = sequence.dict()
    seq_data["id"] = sequence_id_counter
    seq_data["length"] = len(sequence.sequence)
    seq_data["gc_fraction"] = calculate_gc_fraction(sequence.sequence)
    seq_data["created_at"] = datetime.utcnow()
    
    sequences_db.append(seq_data)
    sequence_id_counter += 1
    return seq_data

@app.get("/api/sequences", response_model=List[SequenceModel])
async def list_sequences(gene_id: Optional[int] = None):
    """List sequences, optionally filtered by gene"""
    if gene_id:
        filtered = [s for s in sequences_db if s["gene_id"] == gene_id]
        if not filtered:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No sequences for gene {gene_id}"
            )
        return filtered
    
    if not sequences_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sequences registered"
        )
    return sequences_db

@app.get("/api/sequences/{sequence_id}", response_model=SequenceModel)
async def get_sequence(sequence_id: int):
    """Get sequence by ID"""
    seq = next((s for s in sequences_db if s["id"] == sequence_id), None)
    if not seq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sequence with ID {sequence_id} not found"
        )
    return seq

@app.post("/api/sequences/{sequence_id}/analyze", response_model=SequenceAnalysisResponse)
async def analyze_sequence(sequence_id: int):
    """Analyze a sequence (GC content, reverse complement, properties)"""
    seq = next((s for s in sequences_db if s["id"] == sequence_id), None)
    if not seq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sequence with ID {sequence_id} not found"
        )
    
    sequence = seq["sequence"]
    gc_frac = calculate_gc_fraction(sequence)
    
    return {
        "sequence": sequence[:100] + ("..." if len(sequence) > 100 else ""),
        "length": len(sequence),
        "gc_fraction": gc_frac,
        "gc_percentage": gc_frac * 100,
        "reverse_complement": reverse_complement(sequence)[:100] + "...",
        "properties": get_sequence_properties(sequence),
        "composition": {
            "A": sequence.count("A"),
            "T": sequence.count("T"),
            "G": sequence.count("G"),
            "C": sequence.count("C"),
            "N": sequence.count("N")
        }
    }

@app.post("/api/sequences/analyze", response_model=dict)
async def analyze_raw_sequence(request: SequenceAnalysisRequest):
    """Analyze a raw DNA sequence (no database lookup required)
    
    Args:
        request: Contains the raw DNA sequence
        
    Returns:
        Analysis results including GC fraction, reverse complement, and composition
    """
    sequence = request.sequence.replace('\r', '').replace('\n', '').strip().upper()
    
    if not sequence:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sequence cannot be empty"
        )
    
    # Validate DNA sequence
    valid_chars = set("ATGCN")
    if not all(c in valid_chars for c in sequence):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sequence. Only ATGCN characters are allowed."
        )
    
    gc_frac = calculate_gc_fraction(sequence)
    
    # Count each base
    a_count = sequence.count("A")
    t_count = sequence.count("T")
    g_count = sequence.count("G")
    c_count = sequence.count("C")
    total = len(sequence)
    
    return {
        "length": total,
        "gc_fraction": gc_frac,
        "reverse_complement": reverse_complement(sequence),
        "composition": {
            "A": a_count,
            "T": t_count,
            "G": g_count,
            "C": c_count,
        },
        "composition_percent": {
            "A": (a_count / total) * 100 if total > 0 else 0,
            "T": (t_count / total) * 100 if total > 0 else 0,
            "G": (g_count / total) * 100 if total > 0 else 0,
            "C": (c_count / total) * 100 if total > 0 else 0,
        }
    }

@app.post("/api/sequences/upload", response_model=List[SequenceModel], status_code=status.HTTP_201_CREATED)
async def upload_sequence_file(gene_id: int, file: UploadFile = File(...), seq_type: str = "genomic"):
    """Upload FASTA or GenBank file and create sequences
    
    Supported formats:
    - FASTA (.fasta, .fa, .fna, .txt)
    - GenBank (.gb, .genbank, .gbk)
    
    Args:
        gene_id: Gene ID to associate sequences with
        file: FASTA or GenBank file
        seq_type: Sequence type (genomic, mRNA, protein) - default: genomic
    """
    global sequence_id_counter
    
    # Verify gene exists
    if not any(g["id"] == gene_id for g in genes_db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gene with ID {gene_id} not found"
        )
    
    # Validate file extension
    filename = file.filename.lower() if file.filename else ""
    fasta_extensions = {'.fasta', '.fa', '.fna', '.txt', '.seq'}
    genbank_extensions = {'.gb', '.genbank', '.gbk', '.txt'}
    
    file_ext = ""
    for ext in fasta_extensions.union(genbank_extensions):
        if filename.endswith(ext):
            file_ext = ext
            break
    
    if not file_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {filename}. Supported: {fasta_extensions.union(genbank_extensions)}"
        )
    
    try:
        content = await file.read()
        if not content:
            raise ValueError("File is empty")
        
        file_text = content.decode('utf-8')
        sequences = {}
        
        # Determine file format
        file_text_stripped = file_text.strip()
        
        # Try to detect format if extension is ambiguous
        is_genbank = False
        if file_ext in genbank_extensions and file_ext != '.txt':
            is_genbank = True
        elif file_ext == '.txt':
            # Auto-detect based on content
            is_genbank = file_text_stripped.startswith('LOCUS') or 'FEATURES' in file_text
        
        # Parse sequences based on format
        if is_genbank:
            sequences = read_genbank(file_text)
        else:
            sequences = read_fasta(file_text)
        
        if not sequences:
            raise ValueError(f"No sequences found in {file_ext} file. Please check file format.")
        
        created_sequences = []
        for accession, sequence_str in sequences.items():
            # Validate sequence (only DNA bases allowed)
            valid_bases = set("ATGCNatgcn")
            if not all(base in valid_bases for base in sequence_str):
                raise ValueError(f"Sequence '{accession}' contains invalid DNA bases. Only ATGCN allowed.")
            
            seq_data = {
                "id": sequence_id_counter,
                "gene_id": gene_id,
                "accession": accession,
                "sequence": sequence_str.upper(),
                "description": f"Uploaded from {file.filename} ({len(sequence_str)} bp)",
                "seq_type": seq_type,
                "length": len(sequence_str),
                "gc_fraction": calculate_gc_fraction(sequence_str),
                "created_at": datetime.utcnow()
            }
            sequences_db.append(seq_data)
            created_sequences.append(seq_data)
            sequence_id_counter += 1
        
        return created_sequences
    
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please use UTF-8 encoded text files."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload failed: {str(e)}"
        )


@app.post("/api/sequences/upload-genbank", response_model=List[SequenceModel], status_code=status.HTTP_201_CREATED)
async def upload_genbank_file(gene_id: int, file: UploadFile = File(...), seq_type: str = "genomic"):
    """Upload GenBank (.gb, .gbk) file and create sequences
    
    GenBank format provides additional metadata like features and annotations.
    
    Args:
        gene_id: Gene ID to associate sequences with
        file: GenBank file (.gb, .gbk)
        seq_type: Sequence type (genomic, mRNA, protein) - default: genomic
    """
    global sequence_id_counter
    
    # Verify gene exists
    if not any(g["id"] == gene_id for g in genes_db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gene with ID {gene_id} not found"
        )
    
    # Validate file extension
    filename = file.filename.lower() if file.filename else ""
    genbank_extensions = {'.gb', '.genbank', '.gbk'}
    
    if not any(filename.endswith(ext) for ext in genbank_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected GenBank file (.gb, .gbk, .genbank), got: {filename}"
        )
    
    try:
        content = await file.read()
        if not content:
            raise ValueError("File is empty")
        
        file_text = content.decode('utf-8')
        sequences = read_genbank(file_text)
        
        if not sequences:
            raise ValueError("No sequences found in GenBank file")
        
        created_sequences = []
        for accession, sequence_str in sequences.items():
            # Validate sequence
            valid_bases = set("ATGCNatgcn")
            if not all(base in valid_bases for base in sequence_str):
                raise ValueError(f"Sequence '{accession}' contains invalid DNA bases. Only ATGCN allowed.")
            
            seq_data = {
                "id": sequence_id_counter,
                "gene_id": gene_id,
                "accession": accession,
                "sequence": sequence_str.upper(),
                "description": f"GenBank file: {file.filename} ({len(sequence_str)} bp)",
                "seq_type": seq_type,
                "length": len(sequence_str),
                "gc_fraction": calculate_gc_fraction(sequence_str),
                "created_at": datetime.utcnow()
            }
            sequences_db.append(seq_data)
            created_sequences.append(seq_data)
            sequence_id_counter += 1
        
        return created_sequences
    
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please use UTF-8 encoded files."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GenBank upload failed: {str(e)}"
        )


@app.post("/api/sequences/upload-fasta", response_model=List[SequenceModel], status_code=status.HTTP_201_CREATED)
async def upload_fasta_file(gene_id: int, file: UploadFile = File(...), seq_type: str = "genomic"):
    """Upload FASTA (.fasta, .fa, .fna) file and create sequences
    
    FASTA format is the simplest sequence format containing:
    - Header lines starting with '>'
    - Sequence data on following lines
    
    Args:
        gene_id: Gene ID to associate sequences with
        file: FASTA file (.fasta, .fa, .fna)
        seq_type: Sequence type (genomic, mRNA, protein) - default: genomic
    """
    global sequence_id_counter
    
    # Verify gene exists
    if not any(g["id"] == gene_id for g in genes_db):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gene with ID {gene_id} not found"
        )
    
    # Validate file extension
    filename = file.filename.lower() if file.filename else ""
    fasta_extensions = {'.fasta', '.fa', '.fna', '.txt', '.seq'}
    
    if not any(filename.endswith(ext) for ext in fasta_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected FASTA file (.fasta, .fa, .fna), got: {filename}"
        )
    
    try:
        content = await file.read()
        if not content:
            raise ValueError("File is empty")
        
        file_text = content.decode('utf-8')
        sequences = read_fasta(file_text)
        
        if not sequences:
            raise ValueError("No sequences found in FASTA file. Format must be: >sequence_id\\nATGC...")
        
        created_sequences = []
        for accession, sequence_str in sequences.items():
            # Validate sequence
            valid_bases = set("ATGCNatgcn")
            if not all(base in valid_bases for base in sequence_str):
                raise ValueError(f"Sequence '{accession}' contains invalid DNA bases. Only ATGCN allowed.")
            
            seq_data = {
                "id": sequence_id_counter,
                "gene_id": gene_id,
                "accession": accession,
                "sequence": sequence_str.upper(),
                "description": f"FASTA file: {file.filename} ({len(sequence_str)} bp)",
                "seq_type": seq_type,
                "length": len(sequence_str),
                "gc_fraction": calculate_gc_fraction(sequence_str),
                "created_at": datetime.utcnow()
            }
            sequences_db.append(seq_data)
            created_sequences.append(seq_data)
            sequence_id_counter += 1
        
        return created_sequences
    
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please use UTF-8 encoded files."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"FASTA upload failed: {str(e)}"
        )

# --- PRIMER DESIGN ---

@app.post("/api/primers/design", response_model=PrimerModel)
async def design_primers(sequence_id: int, target_region_start: int, target_region_end: int):
    """Design primers for a target region"""
    seq = next((s for s in sequences_db if s["id"] == sequence_id), None)
    if not seq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sequence with ID {sequence_id} not found"
        )
    
    sequence = seq["sequence"]
    if target_region_end > len(sequence) or target_region_start < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid target region coordinates"
        )
    
    target_seq = sequence[target_region_start:target_region_end]
    forward, reverse = design_primer(target_seq)
    
    return {
        "forward_primer": forward,
        "reverse_primer": reverse,
        "length": len(forward),
        "target_region": target_seq[:50] + "..." if len(target_seq) > 50 else target_seq,
        "tm_value": 4 * (forward.count("G") + forward.count("C")) + 2 * (forward.count("A") + forward.count("T")),
        "gc_content": calculate_gc_fraction(forward) * 100
    }

# --- SNP DETECTION ---

@app.post("/api/variants/detect", response_model=SNPDetectionResponse)
async def detect_variants(reference_seq_id: int, query_seq_id: int):
    """Detect SNPs/variants between reference and query sequences"""
    ref_seq = next((s for s in sequences_db if s["id"] == reference_seq_id), None)
    query_seq = next((s for s in sequences_db if s["id"] == query_seq_id), None)
    
    if not ref_seq or not query_seq:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both sequences not found"
        )
    
    ref_dna = ref_seq["sequence"]
    query_dna = query_seq["sequence"]
    
    mutations = detect_snps(ref_dna, query_dna)
    divergence = (len(mutations) / min(len(ref_dna), len(query_dna))) * 100 if ref_dna and query_dna else 0
    
    return {
        "reference_seq": ref_dna[:100] + "...",
        "query_seq": query_dna[:100] + "...",
        "mutations": mutations[:10],
        "mutation_count": len(mutations),
        "divergence_percentage": divergence
    }

@app.post("/api/sequences/ncbi-download")
async def download_from_ncbi_endpoint(request: NCBIDownloadRequest):
    """Download sequence from NCBI Entrez"""
    try:
        sequences = download_from_ncbi(request.query, request.database, request.max_results)
        return {
            "query": request.query,
            "count": len(sequences),
            "sequences": sequences
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"NCBI download failed: {str(e)}"
        )

# --- NCBI DOWNLOAD & PERSIST ---

class NCBISaveRequest(BaseModel):
    """Request to save NCBI sequence to database"""
    gene_symbol: str = Field(..., description="Gene symbol to associate with sequence")
    gene_name: str = Field(..., description="Full gene name")
    ncbi_accession: str = Field(..., description="NCBI accession (e.g., NM_007294)")
    sequence: str = Field(..., description="DNA sequence from NCBI")
    organism: Optional[str] = None
    description: Optional[str] = None

class NCBISaveResponse(BaseModel):
    """Response when saving NCBI sequence"""
    gene_id: int
    sequence_id: int
    message: str


@app.post("/api/sequences/ncbi-download-and-save", response_model=NCBISaveResponse, status_code=status.HTTP_201_CREATED)
async def download_and_save_from_ncbi(request: NCBISaveRequest):
    """Download sequence from NCBI and save to database"""
    global gene_id_counter, sequence_id_counter
    
    try:
        # Check if gene exists, create if not
        gene = next((g for g in genes_db if g["symbol"] == request.gene_symbol), None)
        if not gene:
            gene_data = {
                "id": gene_id_counter,
                "symbol": request.gene_symbol,
                "name": request.gene_name,
                "ncbi_id": None,
                "chromosome": None,
                "start_position": None,
                "end_position": None,
                "created_at": datetime.utcnow()
            }
            genes_db.append(gene_data)
            gene_id = gene_id_counter
            gene_id_counter += 1
        else:
            gene_id = gene["id"]
        
        # Save sequence
        gc_frac = calculate_gc_fraction(request.sequence)
        seq_data = {
            "id": sequence_id_counter,
            "gene_id": gene_id,
            "accession": request.ncbi_accession,
            "sequence": request.sequence,
            "description": request.description or f"Downloaded from NCBI: {request.ncbi_accession}",
            "organism": request.organism,
            "seq_type": "genomic",
            "length": len(request.sequence),
            "gc_fraction": gc_frac,
            "created_at": datetime.utcnow()
        }
        sequences_db.append(seq_data)
        seq_id = sequence_id_counter
        sequence_id_counter += 1
        
        return {
            "gene_id": gene_id,
            "sequence_id": seq_id,
            "message": f"Sequence {request.ncbi_accession} saved for gene {request.gene_symbol}"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save sequence: {str(e)}"
        )


@app.post("/api/genes/{gene_symbol}/sequences/ncbi-search")
async def search_and_add_ncbi_sequences(gene_symbol: str, request: NCBIDownloadRequest):
    """Search NCBI for gene sequences and add them to database"""
    global sequence_id_counter
    
    try:
        # Find or create gene
        gene = next((g for g in genes_db if g["symbol"] == gene_symbol), None)
        if not gene:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gene {gene_symbol} not found. Create it first."
            )
        
        # Download from NCBI
        sequences = download_from_ncbi(request.query, request.database, request.max_results)
        
        # Add sequences to database
        added = []
        for seq_info in sequences:
            # Check if already exists
            if any(s["accession"] == seq_info["accession"] for s in sequences_db):
                continue
            
            seq_data = {
                "id": sequence_id_counter,
                "gene_id": gene["id"],
                "accession": seq_info.get("accession", "unknown"),
                "sequence": seq_info.get("sequence", ""),
                "description": seq_info.get("description", ""),
                "organism": seq_info.get("organism", ""),
                "seq_type": request.database,
                "length": len(seq_info.get("sequence", "")),
                "gc_fraction": calculate_gc_fraction(seq_info.get("sequence", "")),
                "created_at": datetime.utcnow()
            }
            sequences_db.append(seq_data)
            added.append(seq_data)
            sequence_id_counter += 1
        
        return {
            "gene_symbol": gene_symbol,
            "query": request.query,
            "sequences_found": len(sequences),
            "sequences_added": len(added),
            "added_sequences": added
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"NCBI search failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
