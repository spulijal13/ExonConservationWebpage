"""Explicit search field mappings shared by forms and query construction."""

FILTER_FIELDS = {
    'chromosome': 'chrm', 'gene_name': 'name', 'start_position': 'start_position',
    'end_position': 'end_position', 'length': 'length', 'exon_number': 'exon_number',
    'total_exon': 'total_exon', 'exon_type': 'exon_type', 'splice_site_3': 'ss_score3',
    'splice_site_5': 'ss_score5', 'phylo_p': 'phylo_p', 'ultra_in': 'ultra_in',
    'ultrain_score_20pct_pm3': 'ultrain_score_20pct_pm3',
}

COMPARISON_FIELDS = {
    name: FILTER_FIELDS[name]
    for name in ('length', 'total_exon', 'splice_site_3', 'splice_site_5',
                 'phylo_p', 'ultra_in', 'ultrain_score_20pct_pm3')
}
COMPARISON_CHOICES = [('eq', '='), ('gt', '>'), ('lt', '<'), ('gte', '>='), ('lte', '<=')]
COMPARISON_LOOKUPS = {'eq': 'exact', 'gt': 'gt', 'lt': 'lt', 'gte': 'gte', 'lte': 'lte'}


def filter_exons(query, data):
    """Apply validated SearchForm data without evaluating the queryset."""
    # Coordinate bounds select fully contained exons, not all overlaps.
    filters = {}
    for field, lookup in (
        ('chromosome', 'chrm'), ('gene_name', 'name__icontains'),
        ('start_position', 'start_position__gte'), ('end_position', 'end_position__lte'),
        ('exon_type', 'exon_type'),
    ):
        value = data.get(field)
        if value is not None and value != '':
            filters[lookup] = value
    # Rank 2 matches '2' and '2_8', but not '20_8'.
    if data.get('exon_number') is not None:
        filters['exon_number__regex'] = rf"^{data['exon_number']}(_|$)"
    for field, column in COMPARISON_FIELDS.items():
        value = data.get(field)
        if value is not None:
            lookup = COMPARISON_LOOKUPS[data.get(field + '_comparison') or 'eq']
            filters[f'{column}__{lookup}'] = value
    return query.filter(**filters)
