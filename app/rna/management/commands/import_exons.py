import csv
import hashlib
import math
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from rna.datasets import ASSEMBLIES, map_headers, unknown_headers, suggest_alias
from rna.models import ExonDataset


class Command(BaseCommand):
    help = 'Import/update assembly annotations atomically and discover available columns.'

    def add_arguments(self, parser):
        parser.add_argument('--assembly', choices=ASSEMBLIES, default='hg19')
        parser.add_argument('--path', type=Path)

    @transaction.atomic
    def handle(self, *args, **options):
        assembly = options['assembly']
        model = ASSEMBLIES[assembly]
        path = options.get('path') or settings.BASE_DIR / 'data' / f'{assembly}_exon_conservation.csv'
        digest = hashlib.sha256()
        try:
            with path.open('rb') as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    digest.update(chunk)
        except OSError as exc:
            raise CommandError(str(exc)) from exc
        fingerprint = digest.hexdigest()
        metadata = ExonDataset.objects.filter(assembly=assembly).first()
        if metadata and metadata.source_sha256 == fingerprint and model.objects.count() == metadata.row_count:
            self.stdout.write(f'{assembly}: source unchanged; import skipped.')
            return

        existing = set(model.objects.values_list('exon_id', flat=True))
        fields = list(model._meta.fields)
        seen = set()
        batch = []

        def save_batch():
            model.objects.bulk_create(
                batch, batch_size=1000, update_conflicts=True,
                unique_fields=['exon_id'], update_fields=[field.name for field in fields if not field.primary_key],
            )
            batch.clear()

        def convert(field, value):
            if value is None or value.strip().lower() in ('', 'na', 'nan', 'null', 'none'):
                return None
            value = value.strip()
            if field.name == 'strand':
                value = {'1': '+', '-1': '-'}.get(value, value)
            elif field.name == 'chrm' and not value.startswith('chr'):
                value = 'chr' + value
            result = field.to_python(value)
            if isinstance(result, float) and not math.isfinite(result):
                raise ValueError(f'Non-finite {field.name}')
            return result

        try:
            with path.open(newline='', encoding='utf-8-sig') as source:
                reader = csv.DictReader(source)
                headers = reader.fieldnames or []
                if len(headers) != len(set(headers)):
                    raise ValueError('Duplicate CSV header names are ambiguous.')
                mapping = map_headers(headers, model)
                required = {'exon_id', 'chrm', 'start_position', 'end_position', 'strand'}
                if required - mapping.keys():
                    raise ValueError(f'Missing required columns: {sorted(required - mapping.keys())}')
                for header in unknown_headers(headers, mapping):
                    suggestion = suggest_alias(header)
                    self.stdout.write(f'Ignored column {header!r}' + (f'; possible alias for {suggestion!r}—confirm in datasets.py.' if suggestion else '.'))
                for line, row in enumerate(reader, 2):
                    values = {}
                    for field in fields:
                        candidates = [convert(field, row.get(header)) for header in mapping.get(field.name, [])]
                        present = [value for value in candidates if value is not None]
                        if present and any(value != present[0] for value in present):
                            raise ValueError(f'Conflicting aliases for {field.name} on line {line}')
                        values[field.name] = present[0] if present else None
                    if any(values[key] is None for key in required):
                        raise ValueError(f'Missing required value on line {line}')
                    if values['exon_id'] in seen:
                        raise ValueError(f'Duplicate exon_id on line {line}')
                    seen.add(values['exon_id'])
                    batch.append(model(**values))
                    if len(batch) == 1000:
                        save_batch()
                if not seen:
                    raise ValueError('CSV contains no records.')
                if existing and existing != seen:
                    raise ValueError('Existing dataset is incomplete or different; no rows changed. Reconcile exon IDs before importing.')
                if batch:
                    save_batch()
        except (OSError, KeyError, ValueError, ValidationError) as exc:
            raise CommandError(str(exc)) from exc
        ExonDataset.objects.update_or_create(assembly=assembly, defaults={
            'available_fields': list(mapping), 'source_columns': mapping,
            'source_sha256': fingerprint, 'row_count': len(seen),
        })
        self.stdout.write(self.style.SUCCESS(f'{assembly}: imported/updated {len(seen)} exons; {len(mapping)} available columns.'))
