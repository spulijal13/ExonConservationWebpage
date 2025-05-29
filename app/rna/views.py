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
            length_comparison = form.cleaned_data.get('length_comparison')
            exon_number = form.cleaned_data.get('exon_number')
            total_exon = form.cleaned_data.get('total_exon')
            total_exon_comparison = form.cleaned_data.get('total_exon_comparison')
            exon_type = form.cleaned_data.get('exon_type')
            splice_site_3 = form.cleaned_data.get('splice_site_3')
            splice_site_3_comparison = form.cleaned_data.get('splice_site_3_comparison')
            splice_site_5 = form.cleaned_data.get('splice_site_5')
            splice_site_5_comparison = form.cleaned_data.get('splice_site_5_comparison')
            phylo_p = form.cleaned_data.get('phylo_p')
            phylo_p_comparison = form.cleaned_data.get('phylo_p_comparison')
            ultra_in = form.cleaned_data.get('ultra_in')
            ultra_in_comparison = form.cleaned_data.get('ultra_in_comparison')
            

            # Apply filters if values are provided
            if chromosome:
                query = query.filter(chrm=chromosome)
            if gene_name:
                query = query.filter(name__icontains=gene_name)
            if start_position:
                query = query.filter(start_position__gte=start_position)
            if end_position:
                query = query.filter(end_position__lte=end_position)
            if length:
                if length_comparison == 'eq':
                    query = query.filter(length=length)
                elif length_comparison == 'gt':
                    query = query.filter(length__gt=length)
                elif length_comparison == 'lt':
                    query = query.filter(length__lt=length)
                elif length_comparison == 'gte':
                    query = query.filter(length__gte=length)
                elif length_comparison == 'lte':
                    query = query.filter(length__lte=length)
            if exon_number:
                query = query.filter(exon_number__regex=r'^' + str(exon_number) + r'_')
            if total_exon:
                if total_exon_comparison == 'eq':
                    query = query.filter(total_exon=total_exon)
                elif total_exon_comparison == 'gt':
                    query = query.filter(total_exon__gt=total_exon)
                elif total_exon_comparison == 'lt':
                    query = query.filter(total_exon__lt=total_exon)
                elif total_exon_comparison == 'gte':
                    query = query.filter(total_exon__gte=total_exon)
                elif total_exon_comparison == 'lte':
                    query = query.filter(total_exon__lte=total_exon)
            if exon_type:
                query = query.filter(exon_type=exon_type)
            if splice_site_3:
                if splice_site_3_comparison == 'eq':
                    query = query.filter(ss_score3=splice_site_3)
                elif splice_site_3_comparison == 'gt':
                    query = query.filter(ss_score3__gt=splice_site_3)
                elif splice_site_3_comparison == 'lt':
                    query = query.filter(ss_score3__lt=splice_site_3)
                elif splice_site_3_comparison == 'gte':
                    query = query.filter(ss_score3__gte=splice_site_3)
                elif splice_site_3_comparison == 'lte':
                    query = query.filter(ss_score3__lte=splice_site_3)
            if splice_site_5:
                if splice_site_5_comparison == 'eq':
                    query = query.filter(ss_score5=splice_site_5)
                elif splice_site_5_comparison == 'gt':
                    query = query.filter(ss_score5__gt=splice_site_5)
                elif splice_site_5_comparison == 'lt':
                    query = query.filter(ss_score5__lt=splice_site_5)
                elif splice_site_5_comparison == 'gte':
                    query = query.filter(ss_score5__gte=splice_site_5)
                elif splice_site_5_comparison == 'lte':
                    query = query.filter(ss_score5__lte=splice_site_5)
            if phylo_p:
                if phylo_p_comparison == 'eq':
                    query = query.filter(phylo_p=phylo_p)
                elif phylo_p_comparison == 'gt':
                    query = query.filter(phylo_p__gt=phylo_p)
                elif phylo_p_comparison == 'lt':
                    query = query.filter(phylo_p__lt=phylo_p)
                elif phylo_p_comparison == 'gte':
                    query = query.filter(phylo_p__gte=phylo_p)
                elif phylo_p_comparison == 'lte':
                    query = query.filter(phylo_p__lte=phylo_p)
            if ultra_in:
                if ultra_in_comparison == 'eq':
                    query = query.filter(ultra_in=ultra_in)
                elif ultra_in_comparison == 'gt':
                    query = query.filter(ultra_in__gt=ultra_in)
                elif ultra_in_comparison == 'lt':
                    query = query.filter(ultra_in__lt=ultra_in)
                elif ultra_in_comparison == 'gte':
                    query = query.filter(ultra_in__gte=ultra_in)
                elif ultra_in_comparison == 'lte':
                    query = query.filter(ultra_in__lte=ultra_in)
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
                    exon.exon_id, exon.name, exon.chrm, exon.start_position, exon.end_position, exon.info,
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
                response.write(f"{exon.exon_id}, {exon.name}, {exon.chrm}, {exon.start_position}, {exon.end_position}, {exon.info}, "
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