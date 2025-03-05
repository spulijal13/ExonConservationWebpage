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
    exon_number = forms.IntegerField(required=False, label="Exon Number")
    total_exon = forms.IntegerField(required=False, label="Total Exon Number (in gene)")
    total_exon_comparison = forms.ChoiceField(choices=COMPARISON_CHOICES, required=False)
    exon_type = forms.ChoiceField(choices=EXON_TYPE_CHOICES, required=False, label="Exon Type")
    
    
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
        exon_number = clean_data.get('exon_number')
        total_exon = clean_data.get('total_exon')
        total_exon_comparison = clean_data.get('total_exon_comparison')
        exon_type = clean_data.get('exon_type')
        
        # Chromosome can stand by itself, does not matter if strand, start_position or end position are empty.
        # Strand can also stand by itself, but depending on the value of strand start or end position cannot stad by itself.
        # Start and end position depend on the fact that strand is a value and depending on the value one has to be greater than
        # the other.
        
        # The constraints when querying
        if start_position is not None or end_position is not None:
            if start_position >= end_position:
                raise forms.ValidationError("On the positive strand the start position has to be less that end position.")
        
        return clean_data

class DownloadData(forms.Form):
    FILE_FORMAT_CHOICES = [
        ('csv', "CSV"),
        ('txt', 'TXT'),
    ]
    
    file_format = forms.ChoiceField(choices=FILE_FORMAT_CHOICES, required=True, label='Choose Format')
    