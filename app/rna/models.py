from django.db import models

# Create your models here.
class ExonConservation(models.Model):
    '''
    The model that interacts with the database of information so that Django can see and use it
    '''
    
    exon_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    chrm = models.CharField(max_length=50)
    start = models.CharField(max_length=255)
    end = models.CharField(max_length=255)
    info = models.CharField(max_length=255)
    strand = models.CharField(max_length=255)
    length = models.CharField(max_length=255)
    exon_number = models.CharField(max_length=255)
    exon_type = models.CharField(max_length=255)
    previous_intron = models.CharField(max_length=255)
    next_intron = models.CharField(max_length=255)
    ss_score3 = models.CharField(max_length=255)
    ss_score5 = models.CharField(max_length=255)
    phastcons_100 = models.CharField(max_length=255)
    ultra_in = models.CharField(max_length=255)
    prime3 = models.CharField(max_length=255)
    prime5 =models.CharField(max_length=255)
    cassette = models.CharField(max_length=255)
    const = models.CharField(max_length=255)
    similarity_score = models.CharField(max_length=255)
    phylo_p = models.CharField(max_length=255)
    gene_phylo_p = models.CharField(max_length=255)
    genes_ultra = models.CharField(max_length=255)
    
    class Meta:
        # defines the database that should be read when adding information to each of the following values.
        db_table = 'rna_exonconservation'
        managed = False

    def __str__(self) -> str:
        return self.exon_id
