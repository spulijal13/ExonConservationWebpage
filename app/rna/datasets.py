"""Assembly routing and explicit, punctuation-insensitive CSV field aliases."""
import re
from difflib import get_close_matches

from .models import ExonConservation, Hg38ExonConservation, ExonDataset

ASSEMBLIES = {'hg19': ExonConservation, 'hg38': Hg38ExonConservation}

# Alias order prefers already-normalized CSV columns. Canonical names also work.
ALIASES = {
    'exon_id': ('exon_stable_id', 'Exon stable ID', 'exon_id', 'id'),
    'name': ('gene_name', 'Gene name', 'name'),
    'chrm': ('chromosome_clean', 'chrm', 'chromosome', 'Chromosome/scaffold name'),
    'start_position': ('exon_start', 'Exon region start (bp)', 'start_position', 'start'),
    'end_position': ('exon_end', 'Exon region end (bp)', 'end_position', 'end'),
    'strand': ('strand_clean', 'strand'),
    'length': ('exon_length', 'length'),
    'exon_number': ('exon_rank', 'Exon rank in transcript', 'exon_number'),
    'total_exon': ('total_exon', 'total_exons', 'total_exon_count', 'exon_count'),
    'exon_type': ('exon_type',),
    'previous_intron': ('previous_intron', 'previous_intron_length'),
    'next_intron': ('next_intron', 'next_intron_length'),
    'ss_score3': ('3prime_ss_score', 'ss_score3', '3ss_score', '3prime_splice_site_score'),
    'ss_score5': ('5prime_ss_score', 'ss_score5', '5ss_score', '5prime_splice_site_score'),
    'phastcons_100': ('phastcons_100', 'phastcons100', 'phastcons100_score'),
    'ultra_in': ('ultra_in', 'ultra_in_score'),
    'prime3': ('prime3', '3p'),
    'prime5': ('prime5', '5p'),
    'const': ('const', 'constant', 'constitutive'),
    'phylo_p': ('phylo_p', 'phylop', 'phylop_score'),
    'gene_phylo_p': ('gene_phylo_p', 'gene_phylop_score'),
    'genes_ultra': ('genes_ultra', 'gene_ultra'),
}


def normalize_header(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())


def map_headers(headers, model):
    """Return all matching aliases so conflicting duplicate columns can be rejected."""
    mapping = {}
    for field in model._meta.fields:
        matches = []
        for alias in (*ALIASES.get(field.name, ()), field.name):
            for header in headers:
                if normalize_header(header) == normalize_header(alias) and header not in matches:
                    matches.append(header)
        if matches:
            mapping[field.name] = matches
    return mapping


def unknown_headers(headers, mapping):
    used = {header for matches in mapping.values() for header in matches}
    return [header for header in headers if header and header not in used]


def suggest_alias(header):
    known = {normalize_header(alias): field for field, aliases in ALIASES.items() for alias in aliases}
    matches = get_close_matches(normalize_header(header), known, n=1, cutoff=0.8)
    return known[matches[0]] if matches else None


def dataset_state(assembly):
    record = ExonDataset.objects.filter(assembly=assembly).first()
    if record:
        # Read the fingerprint from SQL on every request so imports in another
        # process invalidate even process-local caches immediately.
        return record.available_fields, record.source_sha256
    # Preserve access to an existing hg19 database until its first metadata import.
    fields = [field.name for field in ExonConservation._meta.fields] if assembly == 'hg19' else []
    return fields, None
