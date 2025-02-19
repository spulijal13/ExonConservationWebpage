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
    STRAND_CHOICES = [("", "-- SELECT STRAND --")]

    # Values from the views file that can be searched through, defines the type of selection as well. (i.e. choice, type)
    chromosome = forms.ChoiceField(choices=CHROMOSOME_CHOICES, required=False, label="Chromosome #")
    strand = forms.ChoiceField(choices=STRAND_CHOICES, required=False, label='Strand')
    start_position = forms.IntegerField(required=False, label='Starting Position')
    end_position = forms.IntegerField(required=False, label="Ending Position")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        print("Initializing SearchForm...")

        chromosome_choices = list(ExonConservation.objects.values_list('chrm', flat=True).distinct())
        strand_choices = list(ExonConservation.objects.values_list('strand', flat=True).distinct())

        if chromosome_choices:
            self.fields['chromosome'].choices += sorted([(chrm, chrm) for chrm in chromosome_choices])

        if strand_choices:
            self.fields['strand'].choices += [(strand, strand) for strand in strand_choices]
    
    def clean(self):
        # Gets the data using the information that is typed in.
        clean_data = super().clean()
        
        chromosome = clean_data.get('chromosome')
        start_position = clean_data.get('start_position')
        end_position = clean_data.get('end_position')
        strand = clean_data.get("strand")
        
        # Chromosome can stand by itself, does not matter if strand, start_position or end position are empty.
        # Strand can also stand by itself, but depending on the value of strand start or end position cannot stad by itself.
        # Start and end position depend on the fact that strand is a value and depending on the value one has to be greater than
        # the other.
        
        # The constraints when querying
        if start_position is not None or end_position is not None:
            if strand is None:
                raise forms.ValidationError("Need to give a value for strand if start or edn position is given.")
            if start_position is None or end_position is None:
                raise forms.ValidationError("Provide both start and end position if one if given.") # can edit out, but keep simple at first.
            if strand == '+' and start_position >= end_position:
                raise forms.ValidationError("On the positive strand the start position has to be less that end position.")
            if strand == '-' and start_position <=  end_position:
                raise forms.ValidationError("On the negative strand the start position has to be less than the end position")
        
        return clean_data

class DownloadData(forms.Form):
    FILE_FORMAT_CHOICES = [
        ('csv', "CSV"),
        ('txt', 'TXT'),
    ]
    
    file_format = forms.ChoiceField(choices=FILE_FORMAT_CHOICES, required=True, label='Choose Format')
    