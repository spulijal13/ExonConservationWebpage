"""Validate search inputs and show controls for the imported assembly columns."""

from django import forms
from .datasets import ASSEMBLIES, dataset_state
from .query_cache import cached_exons
from .search import COMPARISON_CHOICES, COMPARISON_FIELDS, FILTER_FIELDS

COLUMN_CHOICES = [
    ('exon_id', 'ID'), ('name', 'Gene Name'), ('chrm', 'Chromosome'),
    ('start_position', 'Start'), ('end_position', 'End'), ('info', 'Info'),
    ('strand', 'Strand'), ('length', 'Length'), ('exon_number', 'Exon Number'),
    ('total_exon', 'Total Exons'), ('exon_type', 'Exon Type'),
    ('previous_intron', 'Previous Intron'), ('next_intron', 'Next Intron'),
    ('ss_score3', "3' Splice Site Score"), ('ss_score5', "5' Splice Site Score"),
    ('phastcons_100', 'Phastcons100'), ('ultra_in', 'Ultra In Score'),
    ('prime3', "3'"), ('prime5', "5'"), ('cassette', 'Cassette'),
    ('const', 'Constant'), ('similarity_score', 'Similarity Score'),
    ('phylo_p', 'Phylo P'), ('gene_phylo_p', 'Gene Phylo P'), ('genes_ultra', 'Genes Ultra'),
    ('gene_stable_id', 'Gene Stable ID'), ('gene_type', 'Gene Type'),
    ('ultrain_score_20pct_pm3', 'Ultra In Score'),
    ('ultrain_normalized', 'Ultra Normalized Score'),
    ('ultrain_evaluation_coverage', 'Ultra Evaluation Coverage'),
    ('ultrain_panel_size', 'Ultra Panel Size'),
]


class SearchForm(forms.Form):
    """Validate filters and expose only annotations available for the assembly."""

    CHROMOSOME_CHOICES = [("", "-- SELECT CHROMOSOME --")]
    EXON_TYPE_CHOICES = [("", "-- SELECT EXON TYPE --")]

    chromosome = forms.ChoiceField(choices=CHROMOSOME_CHOICES, required=False, label="Chromosome")
    gene_name = forms.CharField(required=False, label='Gene Name')
    start_position = forms.IntegerField(required=False, label='Starting Position')
    end_position = forms.IntegerField(required=False, label="Ending Position")
    length = forms.IntegerField(required=False, label="Exon Length")
    length_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, required=False, label='Length Comparison')
    exon_number = forms.IntegerField(required=False, label="Exon Number")
    total_exon = forms.IntegerField(required=False, label="Total Exon Number (in gene)")
    total_exon_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, required=False, label='Total Exon Comparison')
    exon_type = forms.ChoiceField(choices=EXON_TYPE_CHOICES, required=False, label="Exon Type")
    splice_site_3 = forms.FloatField(required=False, label="3' Splice Site Score")
    splice_site_3_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, required=False, label="3' Splice Site Comparison")
    splice_site_5 = forms.FloatField(required=False, label="5' Splice Site Score")
    splice_site_5_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, required=False, label="5' Splice Site Comparison")
    phylo_p = forms.FloatField(required=False, label='Phylo P Score')
    phylo_p_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, required=False, label='Phylo P Score Comparison')
    ultra_in = forms.IntegerField(required=False, label='Ultra In Score')
    ultra_in_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, required=False, label='Ultra In Score Comparison')

    columns = forms.MultipleChoiceField(
        choices=COLUMN_CHOICES, widget=forms.CheckboxSelectMultiple,
        initial=[name for name, _ in COLUMN_CHOICES],
        error_messages={'required': 'Select at least one column.'},
    )

    ultrain_score_20pct_pm3 = forms.IntegerField(required=False, label='Ultra In Score')
    ultrain_score_20pct_pm3_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, required=False)

    def __init__(self, *args, assembly='hg19', **kwargs):
        available, self.cache_revision = dataset_state(assembly)
        self.available = set(available)
        choices = [(name, label) for name, label in COLUMN_CHOICES if name in self.available]
        data = args[0] if args else kwargs.pop('data', None)
        data = self.with_default_columns(data, choices)
        super().__init__(data, *args[1:], **kwargs)
        self.fields['columns'].choices = choices
        self.fields['columns'].initial = [name for name, _ in choices]
        for field, column in FILTER_FIELDS.items():
            if column not in self.available:
                self.fields.pop(field, None)
                self.fields.pop(field + '_comparison', None)
        self.load_dropdown_choices(assembly)
        for field in FILTER_FIELDS:
            comparison = field + '_comparison'
            if comparison in self.fields:
                self.fields[comparison].label = self.fields[field].label + ' comparison'
        for name, field in self.fields.items():
            if name != 'columns':
                field.widget.attrs['aria-describedby'] = f'id_{name}_errors'
        self.fields['columns'].widget.attrs['aria-describedby'] = 'columns-help id_columns_errors'
        self.filter_rows = [
            (self[field], self[field + '_comparison'] if field + '_comparison' in self.fields else None)
            for field in FILTER_FIELDS if field in self.fields
        ]

    @staticmethod
    def with_default_columns(data, choices):
        """Preserve legacy links while distinguishing an explicitly empty selection."""
        if data is not None and 'columns_present' not in data and 'columns' not in data:
            data = data.copy()
            columns = [name for name, _ in choices]
            if hasattr(data, 'setlist'):
                data.setlist('columns', columns)
            else:
                data['columns'] = columns
        return data

    def load_dropdown_choices(self, assembly):
        model = ASSEMBLIES[assembly]
        for field, column in [('chromosome', 'chrm'), ('exon_type', 'exon_type')]:
            if field in self.fields:
                values = model.objects.exclude(**{column + '__isnull': True}).exclude(**{column: ''}).values_list(column, flat=True).distinct()
                choices = cached_exons(assembly, self.cache_revision, 'choices', column, lambda: sorted(values))
                self.fields[field].choices = list(self.fields[field].choices) + [(value, value) for value in choices]

    def clean(self):
        data = super().clean()
        for field in COMPARISON_FIELDS:
            if data.get(field) is not None and not data.get(field + '_comparison'):
                data[field + '_comparison'] = 'eq'
        start, end = data.get('start_position'), data.get('end_position')
        if start is not None and end is not None and start > end:
            raise forms.ValidationError('Starting position must not exceed ending position.')
        return data

