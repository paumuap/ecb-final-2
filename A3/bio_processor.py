"""Biopython-based DNA sequence processing utilities"""

from Bio import SeqIO, Entrez
from Bio.SeqUtils import gc_fraction, molecular_weight
from typing import Dict, List, Tuple
import io

Entrez.email = "bioinformatics@ecb.local"

# ============== File I/O ==============

def read_fasta(fasta_content: str) -> Dict[str, str]:
    """Read FASTA format and return sequences
    
    Args:
        fasta_content: FASTA file content as string
    
    Returns:
        Dictionary of {accession: sequence}
    """
    sequences = {}
    fasta_io = io.StringIO(fasta_content)
    
    for record in SeqIO.parse(fasta_io, "fasta"):
        sequences[record.id] = str(record.seq).upper()
    
    return sequences

def read_genbank(genbank_content: str) -> Dict[str, str]:
    """Read GenBank format and return sequences
    
    Args:
        genbank_content: GenBank file content as string
    
    Returns:
        Dictionary of {accession: sequence}
    """
    sequences = {}
    gb_io = io.StringIO(genbank_content)
    
    for record in SeqIO.parse(gb_io, "genbank"):
        sequences[record.id] = str(record.seq).upper()
    
    return sequences

# ============== Sequence Analysis ==============

def calculate_gc_fraction(sequence: str) -> float:
    """Calculate GC fraction (0.0 to 1.0)"""
    seq_upper = sequence.upper()
    gc_count = seq_upper.count("G") + seq_upper.count("C")
    return gc_count / len(sequence) if sequence else 0.0

def reverse_complement(sequence: str) -> str:
    """Get reverse complement of DNA sequence"""
    complement_map = {"A": "T", "T": "A", "G": "C", "C": "G", "N": "N"}
    seq_upper = sequence.upper()
    complement = "".join(complement_map.get(base, "N") for base in seq_upper)
    return complement[::-1]

def transcribe_to_rna(sequence: str) -> str:
    """Transcribe DNA sequence to RNA (T -> U)"""
    return sequence.upper().replace("T", "U")

def get_sequence_properties(sequence: str) -> dict:
    """Get various sequence properties"""
    seq_upper = sequence.upper()
    
    return {
        "length": len(sequence),
        "gc_percentage": calculate_gc_fraction(sequence) * 100,
        "at_percentage": (1 - calculate_gc_fraction(sequence)) * 100,
        "a_count": seq_upper.count("A"),
        "t_count": seq_upper.count("T"),
        "g_count": seq_upper.count("G"),
        "c_count": seq_upper.count("C"),
        "n_count": seq_upper.count("N"),
        "is_valid": all(base in "ATGCN" for base in seq_upper)
    }

# ============== Primer Design ==============

def design_primer(target_seq: str, primer_length: int = 20) -> Tuple[str, str]:
    """Design forward and reverse primers using Wallace's rule
    
    Wallace's rule: Tm = 4(G+C) + 2(A+T)
    
    Args:
        target_seq: Target DNA sequence
        primer_length: Desired primer length (default 20bp)
    
    Returns:
        Tuple of (forward_primer, reverse_primer)
    """
    seq_upper = target_seq.upper()
    
    if len(seq_upper) < primer_length:
        primer_length = len(seq_upper)
    
    # Forward primer: first primer_length bases
    forward = seq_upper[:primer_length]
    
    # Reverse primer: reverse complement of last primer_length bases
    reverse = reverse_complement(seq_upper[-primer_length:])
    
    return forward, reverse

def calculate_tm_wallace(primer_seq: str) -> float:
    """Calculate melting temperature using Wallace's rule
    
    Tm = 4(G+C) + 2(A+T) for primers <= 13 bp
    For longer primers, use more complex formula
    """
    primer_upper = primer_seq.upper()
    gc_count = primer_upper.count("G") + primer_upper.count("C")
    at_count = primer_upper.count("A") + primer_upper.count("T")
    
    if len(primer_seq) <= 13:
        return 4 * gc_count + 2 * at_count
    else:
        # Approximate formula for longer primers
        return 64.9 + (41 * (gc_count - 16.4) / len(primer_seq))

# ============== Variant Detection ==============

def detect_snps(reference: str, query: str, min_alignment: bool = True) -> List[dict]:
    """Detect SNPs/variants between reference and query sequences
    
    Args:
        reference: Reference DNA sequence
        query: Query DNA sequence to compare
        min_alignment: Align sequences if different lengths
    
    Returns:
        List of mutation details
    """
    ref_upper = reference.upper()
    query_upper = query.upper()
    
    # Simple alignment: truncate to shorter sequence
    min_len = min(len(ref_upper), len(query_upper))
    ref_aligned = ref_upper[:min_len]
    query_aligned = query_upper[:min_len]
    
    mutations = []
    for i, (ref_base, query_base) in enumerate(zip(ref_aligned, query_aligned)):
        if ref_base != query_base and ref_base in "ATGC" and query_base in "ATGC":
            mutations.append({
                "position": i + 1,
                "reference": ref_base,
                "query": query_base,
                "mutation_type": f"{ref_base}>{query_base}",
                "codon_position": (i % 3) + 1 if i % 3 >= 0 else 1
            })
    
    return mutations

# ============== NCBI Integration ==============

def download_from_ncbi(query: str, database: str = "nucleotide", max_results: int = 5) -> List[dict]:
    """Download sequences from NCBI using Entrez
    
    Args:
        query: NCBI query string or accession number
        database: NCBI database (nucleotide, protein, taxonomy)
        max_results: Maximum number of results
    
    Returns:
        List of sequence information
    """
    try:
        # Search NCBI
        handle = Entrez.esearch(db=database, term=query, retmax=max_results)
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record["IdList"]
        results = []
        
        # Fetch details for each result
        for seq_id in id_list[:max_results]:
            handle = Entrez.efetch(db=database, id=seq_id, rettype="fasta", retmode="text")
            fasta_content = handle.read()
            handle.close()
            
            # Parse FASTA
            fasta_io = io.StringIO(fasta_content)
            for seq_record in SeqIO.parse(fasta_io, "fasta"):
                results.append({
                    "accession": seq_record.id,
                    "description": seq_record.description,
                    "length": len(seq_record.seq),
                    "sequence": str(seq_record.seq)[:200] + "..." if len(seq_record.seq) > 200 else str(seq_record.seq)
                })
        
        return results
    
    except Exception as e:
        raise ValueError(f"NCBI download failed: {str(e)}")

# ============== Codon Utilities ==============

CODON_TABLE = {
    'TTT': 'F', 'TTC': 'F', 'TTA': 'L', 'TTG': 'L',
    'TCT': 'S', 'TCC': 'S', 'TCA': 'S', 'TCG': 'S',
    'TAT': 'Y', 'TAC': 'Y', 'TAA': '*', 'TAG': '*',
    'TGT': 'C', 'TGC': 'C', 'TGA': '*', 'TGG': 'W',
    'CTT': 'L', 'CTC': 'L', 'CTA': 'L', 'CTG': 'L',
    'CCT': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
    'CAT': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
    'CGT': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
    'ATT': 'I', 'ATC': 'I', 'ATA': 'I', 'ATG': 'M',
    'ACT': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
    'AAT': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
    'AGT': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
    'GTT': 'V', 'GTC': 'V', 'GTA': 'V', 'GTG': 'V',
    'GCT': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
    'GAT': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
    'GGT': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G'
}

def translate_dna(sequence: str) -> str:
    """Translate DNA sequence to protein
    
    Args:
        sequence: DNA sequence (ATG start codon assumed)
    
    Returns:
        Protein sequence in single letter code
    """
    seq_upper = sequence.upper().replace("U", "T")
    protein = ""
    
    for i in range(0, len(seq_upper) - 2, 3):
        codon = seq_upper[i:i+3]
        if len(codon) == 3:
            amino_acid = CODON_TABLE.get(codon, "X")
            protein += amino_acid
            if amino_acid == "*":
                break
    
    return protein

def find_orfs(sequence: str, min_length: int = 100) -> List[dict]:
    """Find open reading frames in sequence
    
    Args:
        sequence: DNA sequence to search
        min_length: Minimum ORF length in nucleotides
    
    Returns:
        List of ORF locations and translations
    """
    seq_upper = sequence.upper()
    orfs = []
    
    # Search for ATG start codons
    for i in range(len(seq_upper) - 2):
        if seq_upper[i:i+3] == "ATG":
            # Find stop codon
            for j in range(i + 3, len(seq_upper) - 2, 3):
                codon = seq_upper[j:j+3]
                if codon in ["TAA", "TAG", "TGA"]:
                    orf_length = j + 3 - i
                    if orf_length >= min_length:
                        orf_seq = seq_upper[i:j+3]
                        translation = translate_dna(orf_seq)
                        orfs.append({
                            "start": i,
                            "end": j + 3,
                            "length": orf_length,
                            "sequence": orf_seq,
                            "protein": translation
                        })
                    break
    
    return orfs
