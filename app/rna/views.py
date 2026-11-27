from django.shortcuts import render
from .datasets import ASSEMBLIES
from .query_cache import cached_exons
from .forms import SearchForm, DownloadData, COLUMN_CHOICES
import csv
from django.http import StreamingHttpResponse, JsonResponse, HttpResponseBadRequest

def exon_search(request):
    """
    View function for searching exon data only when the user presses the search button.
    """
    assembly = request.GET.get('assembly', 'hg19')
    if assembly not in ASSEMBLIES:
        return HttpResponseBadRequest('Unknown genome assembly.')
    model = ASSEMBLIES[assembly]
    exons = model.objects.none()
    form = SearchForm(request.GET or None, assembly=assembly)
    download_form = DownloadData(request.GET or None)

    if request.GET:  # Check if the request has GET parameters
        if form.is_valid():


            # Start filtering from all ExonConservation objects
            query = model.objects.all()
            
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
            if start_position is not None:
                query = query.filter(start_position__gte=start_position)
            if end_position is not None:
                query = query.filter(end_position__lte=end_position)
            if length is not None:
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
            if exon_number is not None:
                query = query.filter(exon_number__regex=r'^' + str(exon_number) + r'(_|$)')
            if total_exon is not None:
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
            if splice_site_3 is not None:
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
            if splice_site_5 is not None:
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
            if phylo_p is not None:
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
            if ultra_in is not None:
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
            hg38_ultra = form.cleaned_data.get('ultrain_score_20pct_pm3')
            if hg38_ultra is not None:
                comparison = form.cleaned_data['ultrain_score_20pct_pm3_comparison']
                lookup = 'exact' if comparison == 'eq' else comparison
                query = query.filter(**{'ultrain_score_20pct_pm3__' + lookup: hg38_ultra})
            exons = query

    
    exons = exons.order_by('exon_id')
    selected = form.cleaned_data.get('columns', []) if form.is_bound else [name for name, _ in form.fields['columns'].choices]
    fields = [name for name, _ in COLUMN_CHOICES if name in selected]
    headers = [label for name, label in COLUMN_CHOICES if name in selected]
    file_format = request.GET.get('download_format') if 'download' in request.GET else request.GET.get('file_format')
    if file_format in ('csv', 'txt') and form.is_valid():

        class Echo:
            def write(self, value):
                return value

        def rows():
            writer = csv.writer(Echo())
            yield writer.writerow(fields)
            for row in exons.values_list(*fields).iterator(chunk_size=2000):
                yield writer.writerow(row)

        response = StreamingHttpResponse(
            rows(), content_type='text/csv' if file_format == 'csv' else 'text/plain'
        )
        response['Content-Disposition'] = f'attachment; filename="{assembly}_exon_conservation.{file_format}"'
        return response

    # SQL and parameters distinguish filters and prevent different searches sharing rows.
    # Empty/unbound/invalid searches bypass caching entirely.
    can_cache = form.is_bound and form.is_valid() and bool(fields)
    revision = form.cache_revision if can_cache else None
    identity = exons.query.sql_with_params() if can_cache else None

    def result_rows(offset, size):
        return cached_exons(assembly, revision, 'rows', [identity, fields, offset, size],
                           lambda: list(exons.values_list(*fields)[offset:offset + size]))

    # Keep both the response and browser table bounded, even for all exons.
    window_size = 200
    if request.GET.get('results_window') == '1':
        if not form.is_valid():
            return JsonResponse({'error': 'Invalid search filters or columns.'}, status=400)
        try:
            offset = int(request.GET.get('offset', '0'))
            if offset < 0 or offset > 2147483647:
                raise ValueError
        except ValueError:
            return JsonResponse({'error': 'Invalid row offset.'}, status=400)
        return JsonResponse({
            'rows': result_rows(offset, window_size),
        })

    total = cached_exons(assembly, revision, 'count', identity, exons.count) if fields else 0
    initial_rows = result_rows(0, window_size) if fields else []
    return render(request, 'build.html', {
        'form': form,
        'assembly': assembly,
        'assemblies': list(ASSEMBLIES),
        'exons': initial_rows,
        'result_count': total,
        'results_data': {'rows': initial_rows, 'total': total, 'columns': len(fields)},
        'headers': headers,
        'download_form': download_form,
    })
