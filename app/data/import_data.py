import os
import sys
import django

sys.path.append('/usr/src/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exon.settings')  # Update to your actual settings module
django.setup()

from rna.models import ExonConservation
import csv



csv_file = 'data/Exon_Conservation_Share_Split.csv'

with open(csv_file, 'r') as file:
    
    reader = csv.DictReader(file)
    for row in reader:
        ExonConservation.objects.create(
            exon_id=row['exon_id'],
            name=row['name'],
            chrm=row['chrm'],
            start=row['start'],
            end=row['end'],
            info=row['info'],
            strand=row['strand'],
            length=row['length'],
            exon_number=row['exon_number'],
            total_exon=row['total_exon'],
            exon_type=row['exon_type'],
            previous_intron=row['previous_intron'],
            next_intron=row['next_intron'],
            ss_score3=row['ss_score3'],
            ss_score5=row['ss_score5'],
            phastcons_100=row['phastcons_100'],
            ultra_in=row['ultra_in'],
            prime3=row['prime3'],
            prime5=row['prime5'],
            cassette=row['cassette'],
            const=row['const'],
            similarity_score=row['similarity_score'],
            phylo_p=row['phylo_p'],
            gene_phylo_p=row['gene_phylo_p'],
            genes_ultra=row['genes_ultra']
        )

print("Data import completed successfully!")