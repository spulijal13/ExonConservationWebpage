"""Stream complete query results without caching or materializing all rows."""
import csv

from django.http import StreamingHttpResponse


class Echo:
    def write(self, value):
        return value


def export_exons(exons, fields, assembly, file_format):
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
