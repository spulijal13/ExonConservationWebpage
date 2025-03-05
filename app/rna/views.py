from django.shortcuts import render
from .models import ExonConservation
from .forms import SearchForm, DownloadData
import csv
from django.db.models import IntegerField, F, Value
from django.db.models.functions import Cast, Substr, StrIndex
from django.http import HttpResponse

def exon_search(request):
    """
    View function for searching exon data only when the user presses the search button.
    """
    exons = ExonConservation.objects.none()  # Initialize with an empty QuerySet
    form = SearchForm(request.GET or None)
    download_form = DownloadData(request.GET or None)

    if request.GET:  # Check if the request has GET parameters
        if form.is_valid():
            print("Form Data:", form.cleaned_data)  # Debugging line

            # Start filtering from all ExonConservation objects
            query = ExonConservation.objects.all()
            
            chromosome = form.cleaned_data.get('chromosome')
            gene_name = form.cleaned_data.get('gene_name')
            start_position = form.cleaned_data.get('start_position')
            end_position = form.cleaned_data.get('end_position')
            length = form.cleaned_data.get('length')
            exon_number = form.cleaned_data.get('exon_number')
            total_exon = form.cleaned_data.get('total_exon')
            total_exon_comparison = form.cleaned_data.get('total_exon_comparison')
            exon_type = form.cleaned_data.get('exon_type')
            
            

            # Apply filters if values are provided
            if chromosome:
                query = query.filter(chrm=chromosome)
            if gene_name:
                query = query.filter(name=gene_name)
            if start_position:
                query = query.filter(start__gte=start_position)
            if end_position:
                query = query.filter(end__lte=end_position)
            if exon_number:
                query = query.filter(exon_number__regex=r'^' + str(exon_number) + r'_')
            if total_exon:
                if total_exon_comparison == 'eq':
                    query = query.annotate(second_part=Cast(Substr('exon_number', StrIndex('exon_number', Value('_')) + 1), output_field=IntegerField())
                                           ).filter(second_part=total_exon)
                elif total_exon_comparison == 'gt':
                    query = query.annotate(second_part=Cast(Substr('exon_number', StrIndex('exon_number', Value('_')) + 1), output_field=IntegerField())
                                           ).filter(second_part__gt=total_exon)
                elif total_exon_comparison == 'lt':
                    query = query.annotate(second_part=Cast(Substr('exon_number', StrIndex('exon_number', Value('_')) + 1), output_field=IntegerField())
                                           ).filter(second_part__lt=total_exon)
                elif total_exon_comparison == 'gte':
                    query = query.annotate(second_part=Cast(Substr('exon_number', StrIndex('exon_number', Value('_')) + 1), output_field=IntegerField())
                                           ).filter(second_part__gte=total_exon)
                elif total_exon_comparison == 'lte':
                    query = query.annotate(second_part=Cast(Substr('exon_number', StrIndex('exon_number', Value('_')) + 1), output_field=IntegerField())
                                           ).filter(second_part__lte=total_exon)

            exons = query

    # File Download Handling
    if 'file_format' in request.GET and exons.exists():
        file_format = request.GET.get('file_format')
        
        if file_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="data.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'id', 'name', 'chromosome', 'start', 'end', 'gene info', 'strand',
                'length', 'exon_number', 'exon_type', 'previous_intron', 'next_intron',
                "3'_splice_site", "5'_splice_site", 'phastcons100', 'ultra_intron', 
                "3'", "5'", 'cassette', 'constant', 'similarity_score', 
                'phylo_p_score', 'gene_phylo_p_score', 'gene_ultra_score'
            ])
            
            for exon in exons:
                writer.writerow([
                    exon.exon_id, exon.name, exon.chrm, exon.start, exon.end, exon.info,
                    exon.strand, exon.length, exon.exon_number, exon.exon_type, 
                    exon.previous_intron, exon.next_intron, exon.ss_score3, exon.ss_score5,
                    exon.phastcons_100, exon.ultra_in, exon.prime3, exon.prime5, 
                    exon.cassette, exon.const, exon.similarity_score, 
                    exon.phylo_p, exon.gene_phylo_p, exon.genes_ultra
                ])
            
            return response
        
        elif file_format == 'txt':
            response = HttpResponse(content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="data.txt"'
            
            for exon in exons:
                response.write(f"{exon.exon_id}, {exon.name}, {exon.chrm}, {exon.start}, {exon.end}, {exon.info}, "
                               f"{exon.strand}, {exon.length}, {exon.exon_number}, {exon.exon_type}, "
                               f"{exon.previous_intron}, {exon.next_intron}, {exon.ss_score3}, {exon.ss_score5}, "
                               f"{exon.phastcons_100}, {exon.ultra_in}, {exon.prime3}, {exon.prime5}, "
                               f"{exon.cassette}, {exon.const}, {exon.similarity_score}, {exon.phylo_p}, "
                               f"{exon.gene_phylo_p}, {exon.genes_ultra}\n")
            return response
    
    return render(request, 'build.html', {
        'form': form, 
        'exons': exons,  # Will be empty until search is performed
        'download_form': download_form
    })