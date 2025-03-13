import os
import subprocess
from django.db import connection
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.conf import settings


@receiver(post_migrate)
def ensure_table_creation(sender, **kwargs):
    table_name = 'rna_exonconservation'
    with connection.cursor() as cursor:
        db_engine = connection.settings_dict['ENGINE']

        if 'sqlite' in db_engine:
            # SQLite: Check if table exists using sqlite_master
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        elif 'postgresql' in db_engine:
            # PostgreSQL: Check table existence using information_schema
            cursor.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='{table_name}');")
        else:
            print(f"Unsupported database engine: {db_engine}")
            return
        exists = cursor.fetchone()[0]
        
        if not exists:
            cursor.execute("""
                            CREATE TABLE rna_exonconservation (
    exon_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    chrm VARCHAR(50),
    start_position INTEGER,
    end_position INTEGER,
    info VARCHAR(255),
    strand VARCHAR(255),
    length INTEGER,
    exon_number VARCHAR(255),
    total_exon INTEGER,
    exon_type VARCHAR(255),
    previous_intron VARCHAR(255),
    next_intron VARCHAR(255),
    ss_score3 VARCHAR(255),
    ss_score5 VARCHAR(255),
    phastcons_100 VARCHAR(255),
    ultra_in VARCHAR(255),
    prime3 VARCHAR(255),
    prime5 VARCHAR(255),
    cassette VARCHAR(255),
    const VARCHAR(255),
    similarity_score VARCHAR(255),
    phylo_p VARCHAR(255),
    gene_phylo_p VARCHAR(255),
    genes_ultra VARCHAR(255)
);
                               """)
            print(f'{table_name} was missing and has now been created.')
        
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]

        if count == 0:
            print(f"Table '{table_name}' is empty. Running data import script...")

            import_script = os.path.join(settings.BASE_DIR, "data/import_data.py")

            if os.path.exists(import_script):
                subprocess.run(["python", import_script], check=True)
                print("Data import completed successfully.")
            else:
                print(f"Import script '{import_script}' not found!")