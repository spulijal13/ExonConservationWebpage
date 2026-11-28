"""Database fields, search indexes, and per-assembly import metadata."""

from django.db import models
from django.db.models.functions import Upper
from django.contrib.postgres.indexes import GinIndex, OpClass

class ExonFields(models.Model):
    """Annotations shared by both genome assemblies."""
    
    exon_id = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    chrm = models.CharField(max_length=50, null=True, blank=True)
    start_position = models.IntegerField(null=True, blank=True)
    end_position = models.IntegerField(null=True, blank=True)
    info = models.CharField(max_length=255, null=True, blank=True)
    strand = models.CharField(max_length=255, null=True, blank=True)
    length = models.IntegerField(null=True, blank=True)
    exon_number = models.CharField(max_length=255, null=True, blank=True)
    total_exon = models.IntegerField(null=True, blank=True)
    exon_type = models.CharField(max_length=255, null=True, blank=True)
    previous_intron = models.CharField(max_length=255, null=True, blank=True)
    next_intron = models.CharField(max_length=255, null=True, blank=True)
    ss_score3 = models.FloatField(null=True, blank=True)
    ss_score5 = models.FloatField(null=True, blank=True)
    phastcons_100 = models.CharField(max_length=255, null=True, blank=True)
    ultra_in = models.IntegerField(null=True, blank=True)
    prime3 = models.CharField(max_length=255, null=True, blank=True)
    prime5 = models.CharField(max_length=255, null=True, blank=True)
    cassette = models.CharField(max_length=255, null=True, blank=True)
    const = models.CharField(max_length=255, null=True, blank=True)
    similarity_score = models.CharField(max_length=255, null=True, blank=True)
    phylo_p = models.FloatField(null=True, blank=True)
    gene_phylo_p = models.CharField(max_length=255, null=True, blank=True)
    genes_ultra = models.CharField(max_length=255, null=True, blank=True)
    
    class Meta:
        abstract = True

    def __str__(self) -> str:
        return self.exon_id


class ExonConservation(ExonFields):
    class Meta:
        db_table = 'rna_exonconservation'
        indexes = [
            models.Index(fields=['chrm', 'exon_id'], name='hg19_chrm_id_idx'),
            models.Index(fields=['chrm', 'start_position', 'end_position'], name='hg19_coordinates_idx'),
            models.Index(fields=['exon_type', 'exon_id'], name='hg19_type_id_idx'),
            models.Index(fields=['length'], name='hg19_length_idx'),
            models.Index(fields=['total_exon'], name='hg19_total_exon_idx'),
            models.Index(fields=['ss_score3'], name='hg19_ss3_idx'),
            models.Index(fields=['ss_score5'], name='hg19_ss5_idx'),
            models.Index(fields=['phylo_p'], name='hg19_phylop_idx'),
            models.Index(fields=['ultra_in'], name='hg19_ultra_idx'),
            GinIndex(OpClass(Upper('name'), name='gin_trgm_ops'), name='hg19_name_trgm_idx'),
        ]


class Hg38ExonConservation(ExonFields):
    gene_stable_id = models.CharField(max_length=255, null=True, blank=True)
    gene_type = models.CharField(max_length=255, null=True, blank=True)
    ultrain_score_20pct_pm3 = models.IntegerField(null=True, blank=True)
    ultrain_normalized = models.FloatField(null=True, blank=True)
    ultrain_evaluation_coverage = models.FloatField(null=True, blank=True)
    ultrain_panel_size = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'rna_hg38exonconservation'
        indexes = [
            models.Index(fields=['chrm', 'exon_id'], name='hg38_chrm_id_idx'),
            models.Index(fields=['chrm', 'start_position', 'end_position'], name='hg38_coordinates_idx'),
            models.Index(fields=['exon_type', 'exon_id'], name='hg38_type_id_idx'),
            models.Index(fields=['length'], name='hg38_length_idx'),
            models.Index(fields=['total_exon'], name='hg38_total_exon_idx'),
            models.Index(fields=['ss_score3'], name='hg38_ss3_idx'),
            models.Index(fields=['ss_score5'], name='hg38_ss5_idx'),
            models.Index(fields=['phylo_p'], name='hg38_phylop_idx'),
            models.Index(fields=['ultrain_score_20pct_pm3'], name='hg38_ultra_idx'),
            GinIndex(OpClass(Upper('name'), name='gin_trgm_ops'), name='hg38_name_trgm_idx'),
        ]


class ExonDataset(models.Model):
    """Import summary used to choose visible controls and invalidate cached results."""

    assembly = models.CharField(max_length=4, primary_key=True)
    available_fields = models.JSONField(default=list)
    source_columns = models.JSONField(default=dict)
    source_sha256 = models.CharField(max_length=64)
    row_count = models.PositiveIntegerField()
