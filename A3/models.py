"""Tortoise ORM models for Gene and Sequence persistence"""

from tortoise import BaseModel, fields
from datetime import datetime


class Gene(BaseModel):
    """Gene model for storing gene information"""
    id = fields.IntField(pk=True)
    symbol = fields.CharField(max_length=50, unique=True, index=True, description="Gene symbol (e.g., BRCA1)")
    name = fields.CharField(max_length=255, description="Full gene name")
    ncbi_id = fields.CharField(max_length=50, null=True, description="NCBI gene ID")
    chromosome = fields.CharField(max_length=10, null=True, description="Chromosome location")
    start_position = fields.BigIntField(null=True, description="Start position on chromosome")
    end_position = fields.BigIntField(null=True, description="End position on chromosome")
    description = fields.TextField(null=True, description="Gene description")
    sequences = fields.ReverseRelation("Sequence")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "genes"

    def __str__(self):
        return f"{self.symbol} ({self.name})"


class Sequence(BaseModel):
    """Sequence model for storing DNA/RNA sequences"""
    id = fields.IntField(pk=True)
    gene = fields.ForeignKeyField("models.Gene", related_name="sequences", description="Reference to Gene")
    accession = fields.CharField(max_length=50, unique=True, index=True, description="NCBI accession (e.g., NM_007294)")
    sequence = fields.TextField(description="DNA/RNA sequence")
    description = fields.TextField(null=True, description="Sequence description from NCBI")
    organism = fields.CharField(max_length=255, null=True, description="Organism name")
    seq_type = fields.CharField(
        max_length=20,
        default="genomic",
        description="Sequence type: genomic, mRNA, protein"
    )
    gc_fraction = fields.FloatField(null=True, description="GC content fraction (0.0-1.0)")
    gc_percentage = fields.FloatField(null=True, description="GC content percentage")
    length = fields.IntField(null=True, description="Sequence length in bases")
    source = fields.CharField(
        max_length=50,
        default="ncbi",
        description="Source: ncbi, upload, computed"
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "sequences"

    def __str__(self):
        return f"{self.accession} ({self.organism})"


class SequenceAnalysis(BaseModel):
    """Store primer design and analysis results"""
    id = fields.IntField(pk=True)
    sequence = fields.ForeignKeyField("models.Sequence", related_name="analyses", description="Reference to Sequence")
    analysis_type = fields.CharField(
        max_length=50,
        description="Analysis type: primer_design, snp_detection, gc_analysis"
    )
    parameters = fields.JSONField(description="Analysis parameters")
    results = fields.JSONField(description="Analysis results")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "sequence_analyses"

    def __str__(self):
        return f"{self.analysis_type} on {self.sequence.accession}"
