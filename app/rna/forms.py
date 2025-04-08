from django import forms
from .models import ExonConservation
'''
Creates forms that can be viewed and interacted with on the main page.
'''

class SearchForm(forms.Form):
    '''
    This creates the search bar and associated features with that
    '''
    
    # Intializes the list of choices for each of the following values
    CHROMOSOME_CHOICES = [("", "-- SELECT CHROMOSOME --")]
    EXON_TYPE_CHOICES = [("", "-- SELECT EXON TYPE --")]
    COMPARISON_CHOICES = [
        ('eq', '='),
        ('gt', '>'),
        ('lt', '<'),
        ('gte', '>='),
        ('lte', '<=')
    ]

    # Values from the views file that can be searched through, defines the type of selection as well. (i.e. choice, type)
    chromosome = forms.ChoiceField(choices=CHROMOSOME_CHOICES, required=False, label="Chromosome")
    gene_name = forms.CharField(required=False, label='Gene Name')
    start_position = forms.IntegerField(required=False, label='Starting Position')
    end_position = forms.IntegerField(required=False, label="Ending Position")
    length = forms.IntegerField(required=False, label="Exon Length")
    length_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, required=False, label='Length Comaparison')
    exon_number = forms.IntegerField(required=False, label="Exon Number")
    total_exon = forms.IntegerField(required=False, label="Total Exon Number (in gene)")
    total_exon_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, required=False, label='Total Exon Comparison')
    exon_type = forms.ChoiceField(choices=EXON_TYPE_CHOICES, required=False, label="Exon Type")
    splice_site_3 = forms.FloatField(required=False, label="3' Splice Site Score")
    splice_site_3_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, label="3' Splice Site Comparison")
    splice_site_5 = forms.FloatField(required=False, label="5' Splice Site Score")
    splice_site_5_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, label="5' Splice Site Comparison")
    phylo_p = forms.FloatField(required=False, label='Phylo P Score')
    phylo_p_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, label='Phylo P Score Comparison')
    ultra_in = forms.FloatField(required=False, label='Ultra In Score')
    ultra_in_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, label='Ultra In Score Comparison')
    
    
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        print("Initializing SearchForm...")

        chromosome_choices = list(ExonConservation.objects.values_list('chrm', flat=True).distinct())
        
        exon_type_choices = list(ExonConservation.objects.values_list('exon_type', flat=True).distinct())

        if chromosome_choices:
            self.fields['chromosome'].choices += sorted([(chrm, chrm) for chrm in chromosome_choices])
        
        if exon_type_choices:
            self.fields['exon_type'].choices += sorted([(exon_type, exon_type) for exon_type in exon_type_choices])
        
        
    
    def clean(self):
        # Gets the data using the information that is typed in.
        clean_data = super().clean()
        
        chromosome = clean_data.get('chromosome')
        gene_name = clean_data.get('name')
        start_position = clean_data.get('start_position')
        end_position = clean_data.get('end_position')
        length = clean_data.get('length')
        length_comparison = clean_data.get('length_comparison')
        exon_number = clean_data.get('exon_number')
        total_exon = clean_data.get('total_exon')
        total_exon_comparison = clean_data.get('total_exon_comparison')
        exon_type = clean_data.get('exon_type')
        splice_site_3 = clean_data.get('splice_site_3')
        splice_site_3_comparison = clean_data.get('splice_site_5_comparison')
        splice_site_5 = clean_data.get('splice_site_5')
        splice_site_5_comparison = clean_data.get('splice_site_5_comparison')
        phylo_p = clean_data.get('phylo_p')
        phylo_p_comparison = clean_data.get('phylo_p_comparison')
        ultra_in = clean_data.get('ultra_in')
        ultra_in_comparison = clean_data.get('ultra_in_comparison')
        
        return clean_data

class DownloadData(forms.Form):
    FILE_FORMAT_CHOICES = [
        ('csv', "CSV"),
        ('txt', 'TXT'),
    ]
    
    file_format = forms.ChoiceField(choices=FILE_FORMAT_CHOICES, required=True, label='Choose Format')
    