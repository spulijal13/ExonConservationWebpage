"""Handle search-page requests, scrolling requests, and full downloads."""

from django.shortcuts import render
from .datasets import ASSEMBLIES
from .query_cache import cached_exons
from .forms import SearchForm, COLUMN_CHOICES
from .search import filter_exons
from .exports import export_exons
from django.http import JsonResponse, HttpResponseBadRequest

def exon_search(request):
    """
    Serve validated searches as HTML, JSON result windows, or full downloads.
    """
    assembly = request.GET.get('assembly', 'hg19')
    if assembly not in ASSEMBLIES:
        return HttpResponseBadRequest('Unknown genome assembly.')
    model = ASSEMBLIES[assembly]
    exons = model.objects.none()
    form = SearchForm(request.GET or None, assembly=assembly)

    valid_search = form.is_valid()
    if valid_search:
        exons = filter_exons(model.objects.all(), form.cleaned_data)

    exons = exons.order_by('exon_id')
    selected = form.cleaned_data.get('columns', []) if form.is_bound else [name for name, _ in form.fields['columns'].choices]
    fields = [name for name, _ in COLUMN_CHOICES if name in selected]
    headers = [label for name, label in COLUMN_CHOICES if name in selected]
    file_format = request.GET.get('download_format') if 'download' in request.GET else request.GET.get('file_format')
    if file_format in ('csv', 'txt') and valid_search:
        return export_exons(exons, fields, assembly, file_format)

    # SQL and parameters distinguish filters and prevent different searches sharing rows.
    # Empty/unbound/invalid searches bypass caching entirely.
    can_cache = valid_search and bool(fields)
    revision = form.cache_revision if can_cache else None
    identity = exons.query.sql_with_params() if can_cache else None

    def result_rows(offset, size):
        return cached_exons(assembly, revision, 'rows', [identity, fields, offset, size],
                           lambda: list(exons.values_list(*fields)[offset:offset + size]))

    # Keep both the response and browser table bounded, even for all exons.
    window_size = 200
    if request.GET.get('results_window') == '1':
        if not valid_search:
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
    })
