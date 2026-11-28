import csv
import io
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from .forms import SearchForm
from .models import ExonConservation


class ExonTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        with (Path(__file__).resolve().parents[1] / 'data/hg19_exon_conservation.csv').open() as source:
            cls.source_row = next(csv.DictReader(source))
        values = {
            field.name: field.to_python(cls.source_row[field.name])
            for field in ExonConservation._meta.fields
        }
        for index in range(302):
            ExonConservation.objects.create(**dict(values, exon_id=f'test{index:03}', phylo_p=index, ultra_in=index))

    def test_zero_and_numeric_filters(self):
        response = self.client.get('/', {'phylo_p': '0'})
        self.assertEqual(len(response.context['exons']), 1)
        response = self.client.get('/', {'ultra_in': '9', 'ultra_in_comparison': 'gt'})
        self.assertEqual(response.context['result_count'], 292)
        self.assertEqual(len(response.context['exons']), 200)

    def test_selected_columns_and_full_exports(self):
        params = {'gene_name': self.source_row['name'], 'columns_present': '1',
                  'columns': ['name', 'total_exon'], 'page': '2'}
        response = self.client.get('/', params)
        self.assertEqual(len(response.context['exons']), 200)
        self.assertEqual(response.context['result_count'], 302)
        self.assertEqual(response.context['headers'], ['Gene Name', 'Total Exons'])
        self.assertEqual(len(response.context['exons'][0]), 2)
        self.assertNotContains(response, 'Results pages')
        self.assertNotContains(response, '<th>Chromosome</th>')
        for fmt in ('csv', 'txt'):
            response = self.client.get('/', dict(params, download='1', download_format=fmt))
            rows = list(csv.reader(io.StringIO(b''.join(response.streaming_content).decode())))
            self.assertEqual(len(rows), 303)
            self.assertEqual(rows[0], ['name', 'total_exon'])
            self.assertEqual(rows[1], [self.source_row['name'], self.source_row['total_exon']])
            self.assertIn(f'hg19_exon_conservation.{fmt}', response['Content-Disposition'])

    def test_scroll_windows_are_bounded_and_keep_filters_and_columns(self):
        params = {'columns_present': '1', 'columns': ['exon_id', 'phylo_p'],
                  'phylo_p': '9', 'phylo_p_comparison': 'gt'}
        response = self.client.get('/', params)
        self.assertLess(len(response.content), 100000)
        self.assertEqual(response.context['exons'][0], ('test010', 10))
        first = self.client.get('/', dict(params, results_window='1', offset='0')).json()['rows']
        last = self.client.get('/', dict(params, results_window='1', offset='200')).json()['rows']
        self.assertEqual(len(first), 200)
        self.assertEqual(len(last), 92)
        self.assertEqual(last[0], ['test210', 210])
        self.assertEqual(last[-1], ['test301', 301])
        self.assertEqual(len({row[0] for row in first + last}), 292)
        self.assertEqual(self.client.get('/', dict(params, results_window='1', offset='999')).json()['rows'], [])
        for offset in ('-1', 'bad', '999999999999999999999999'):
            self.assertEqual(self.client.get('/', dict(params, results_window='1', offset=offset)).status_code, 400)
        self.assertEqual(self.client.get('/', {'results_window': '1', 'columns': ['invalid']}).status_code, 400)

    def test_column_validation(self):
        for selection in ([], ['invalid_field']):
            response = self.client.get('/', {'columns_present': '1', 'columns': selection,
                                             'download': '1', 'download_format': 'csv'})
            self.assertFalse(response.streaming)
            self.assertIn('columns', response.context['form'].errors)
            self.assertEqual(len(response.context['exons']), 0)

    def test_form_validation(self):
        self.assertTrue(SearchForm({'gene_name': 'MARCHF1'}).is_valid())
        self.assertFalse(SearchForm({'start_position': 10, 'end_position': 1}).is_valid())
        self.assertFalse(SearchForm({'phylo_p': 1, 'phylo_p_comparison': 'invalid'}).is_valid())

    @override_settings(ALLOWED_HOSTS=['localhost', '127.0.0.1', '0.0.0.0'])
    def test_local_hosts(self):
        for host in ('localhost', '127.0.0.1', '0.0.0.0'):
            self.assertEqual(self.client.get('/', HTTP_HOST=f'{host}:8000').status_code, 200)

    def test_import_is_atomic_and_refuses_partial_dataset(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.csv'
            with path.open('w', newline='') as target:
                writer = csv.DictWriter(target, fieldnames=self.source_row)
                writer.writeheader()
                writer.writerow(self.source_row)
            with self.assertRaises(CommandError):
                call_command('import_exons', path=path, stdout=io.StringIO())
            ExonConservation.objects.all().delete()
            original = ExonConservation.objects.bulk_create

            def fail_after_insert(objects, **kwargs):
                original(objects, **kwargs)
                raise RuntimeError('Interrupted import')

            with patch.object(ExonConservation.objects, 'bulk_create', side_effect=fail_after_insert):
                with self.assertRaises(RuntimeError):
                    call_command('import_exons', path=path, stdout=io.StringIO())
            self.assertFalse(ExonConservation.objects.exists())
            call_command('import_exons', path=path, stdout=io.StringIO())
            call_command('import_exons', path=path, stdout=io.StringIO())
            self.assertEqual(ExonConservation.objects.count(), 1)

    def test_accessible_controls_and_results(self):
        from html.parser import HTMLParser

        class Controls(HTMLParser):
            def __init__(self):
                super().__init__()
                self.labels = set()
                self.controls = []
                self.ids = set()

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if 'id' in attrs:
                    self.ids.add(attrs['id'])
                if tag == 'label' and 'for' in attrs:
                    self.labels.add(attrs['for'])
                if tag == 'select' or (tag == 'input' and attrs.get('type') not in ('hidden', 'checkbox')):
                    self.controls.append(attrs)

        response = self.client.get('/', {'phylo_p': '0'})
        parser = Controls()
        parser.feed(response.content.decode())
        for control in parser.controls:
            self.assertIn(control['id'], parser.labels)
            for reference in control.get('aria-describedby', '').split():
                self.assertIn(reference, parser.ids)
        self.assertContains(response, 'Skip to main content')
        self.assertContains(response, 'scope="col"')
        self.assertContains(response, 'aria-rowcount="2"')
        self.assertContains(response, 'aria-rowindex="2"')
        self.assertContains(response, 'tabindex="0" role="region"')
        self.assertNotContains(response, 'onchange=')

    def test_accessible_error_feedback(self):
        response = self.client.get('/', {'length': 'not-a-number'})
        self.assertContains(response, 'id="error-summary"')
        self.assertContains(response, 'href="#id_length"')
        self.assertContains(response, 'aria-invalid="true"')
        self.assertContains(response, 'id="id_length_errors"')



class AssemblyTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.addCleanup(cache.clear)
        from .models import Hg38ExonConservation, ExonDataset
        self.hg38 = Hg38ExonConservation
        self.metadata = ExonDataset
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'hg38.csv'
        self.row = {
            'exon_stable_id': 'shared-id', 'gene_name': 'HG38GENE',
            'gene_stable_id': 'ENSG001', 'chromosome': '1',
            'exon_start': '100', 'exon_end': '200', 'strand': '-1',
            'exon_rank': '2', 'exon_length': '100', 'phylop': 'NA',
            '3prime_ss_score': 'NA', '5prime_ss_score': '0',
            'ultrain_score_20pct_pm3': '15',
        }

    def write_and_import(self):
        with self.path.open('w', newline='') as target:
            writer = csv.DictWriter(target, fieldnames=self.row)
            writer.writeheader()
            writer.writerow(self.row)
        call_command('import_exons', assembly='hg38', path=self.path, stdout=io.StringIO())

    def test_assembly_isolation_and_missing_fields(self):
        ExonConservation.objects.create(exon_id='shared-id', name='HG19GENE', chrm='chr1')
        self.write_and_import()
        obj = self.hg38.objects.get()
        self.assertEqual(obj.chrm, 'chr1')
        self.assertEqual(obj.strand, '-')
        self.assertIsNone(obj.phylo_p)
        self.assertIsNone(obj.ss_score3)
        self.assertEqual(obj.ss_score5, 0)
        self.assertIsNone(obj.total_exon)
        response = self.client.get('/', {'assembly': 'hg38'})
        form = response.context['form']
        self.assertNotIn('total_exon', form.fields)
        self.assertNotIn('exon_type', form.fields)
        self.assertNotIn('ultra_in', form.fields)
        self.assertIn('ultrain_score_20pct_pm3', form.fields)
        self.assertNotIn('phastcons_100', dict(form.fields['columns'].choices))
        self.assertContains(response, 'HG38GENE')
        self.assertNotContains(response, 'HG19GENE')
        response = self.client.get('/', {'assembly': 'hg38', 'exon_number': '2'})
        self.assertEqual(response.context['result_count'], 1)
        for fmt in ('csv', 'txt'):
            response = self.client.get('/', {'assembly': 'hg38', 'columns': ['exon_id', 'name', 'phylo_p'],
                                             'download': '1', 'download_format': fmt})
            rows = list(csv.reader(io.StringIO(b''.join(response.streaming_content).decode())))
            self.assertEqual(rows, [['exon_id', 'name', 'phylo_p'], ['shared-id', 'HG38GENE', '']])
            self.assertIn(f'hg38_exon_conservation.{fmt}', response['Content-Disposition'])
        response = self.client.get('/', {'assembly': 'hg38', 'results_window': '1', 'columns': ['name']})
        self.assertEqual(response.json()['rows'], [['HG38GENE']])
        self.assertEqual(self.client.get('/', {'assembly': 'invalid'}).status_code, 400)

    def test_added_alias_columns_become_available_after_reimport(self):
        self.write_and_import()
        self.row.update({'Total Exons': '4', 'EXON TYPE': 'Internal_Exon', 'PhastCons100': '0.9'})
        self.write_and_import()
        self.assertEqual(self.hg38.objects.count(), 1)
        self.assertEqual(self.hg38.objects.get().total_exon, 4)
        form = SearchForm({'total_exon': '4'}, assembly='hg38')
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIn('total_exon', form.fields)
        self.assertIn('exon_type', form.fields)
        self.assertIn('phastcons_100', dict(form.fields['columns'].choices))
        response = self.client.get('/', {'assembly': 'hg38', 'total_exon': '4'})
        self.assertEqual(response.context['result_count'], 1)
        # Removing a column clears old annotations and hides the filter again.
        del self.row['Total Exons']
        self.write_and_import()
        self.assertIsNone(self.hg38.objects.get().total_exon)
        self.assertNotIn('total_exon', SearchForm(assembly='hg38').fields)

    def test_unknown_or_conflicting_columns_are_not_silently_mapped(self):
        self.row['gene_names'] = 'DO NOT GUESS'
        self.write_and_import()
        self.assertEqual(self.hg38.objects.get().name, 'HG38GENE')
        self.row['Gene name'] = 'CONFLICT'
        with self.assertRaisesMessage(CommandError, 'Conflicting aliases'):
            self.write_and_import()
        self.assertEqual(self.hg38.objects.get().name, 'HG38GENE')


class Hg19CacheTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        from .models import ExonDataset
        cache.clear()
        self.addCleanup(cache.clear)
        ExonConservation.objects.create(exon_id='a', name='ALPHA', chrm='chr1', strand='+', start_position=1, end_position=10)
        ExonConservation.objects.create(exon_id='b', name='BETA', chrm='chr2', strand='+', start_position=20, end_position=30)
        ExonDataset.objects.create(assembly='hg19', source_sha256='test-revision', row_count=2,
                                  available_fields=[field.name for field in ExonConservation._meta.fields])

    def test_repeat_search_only_reads_dataset_version(self):
        params = {'assembly': 'hg19', 'columns': ['exon_id', 'name']}
        first = self.client.get('/', params)
        with self.assertNumQueries(1):
            second = self.client.get('/', params)
        self.assertEqual(first.context['exons'], second.context['exons'])
        self.assertEqual(second.context['result_count'], 2)
        # Initial HTML and scrolling reuse the same window, but not different filters/columns/offsets.
        with self.assertNumQueries(1):
            self.assertEqual(self.client.get('/', dict(params, results_window='1')).json()['rows'], [['a', 'ALPHA'], ['b', 'BETA']])
        response = self.client.get('/', dict(params, chromosome='chr2'))
        self.assertEqual(response.context['exons'], [('b', 'BETA')])
        response = self.client.get('/', dict(params, columns=['name'], results_window='1', offset='1'))
        self.assertEqual(response.json()['rows'], [['BETA']])
        self.assertEqual(self.client.get('/', dict(params, gene_name='MISSING')).context['result_count'], 0)
        with self.assertNumQueries(1):
            self.assertEqual(self.client.get('/', dict(params, gene_name='MISSING')).context['result_count'], 0)

    def test_changed_import_invalidates_existing_cache_without_shared_memory(self):
        from .models import ExonDataset
        from .query_cache import cached_exons
        params = {'assembly': 'hg19', 'columns': ['name']}
        self.client.get('/', params)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'hg19.csv'
            path.write_text('exon_id,name,chrm,start,end,strand\na,NEW,chrX,1,10,+\nb,BETA,chr2,20,30,+\n')
            call_command('import_exons', assembly='hg19', path=path, stdout=io.StringIO())
        response = self.client.get('/', params)
        self.assertEqual(response.context['exons'], [('NEW',), ('BETA',)])
        self.assertIn(('chrX', 'chrX'), response.context['form'].fields['chromosome'].choices)
        self.assertNotIn('phylo_p', response.context['form'].fields)
        self.assertNotEqual(ExonDataset.objects.get(pk='hg19').source_sha256, 'test-revision')
        # There is no need to delete keys in each web worker to invalidate an import.
        with patch('rna.query_cache.cache.get', side_effect=AssertionError('Unversioned data must bypass cache')):
            self.assertEqual(cached_exons('hg38', None, 'count', {}, lambda: 42), 42)

    def test_exports_do_not_use_cached_rows(self):
        params = {'assembly': 'hg19', 'columns': ['name']}
        self.client.get('/', params)
        ExonConservation.objects.filter(pk='a').update(name='FRESH')
        response = self.client.get('/', dict(params, download='1', download_format='csv'))
        self.assertIn('FRESH', b''.join(response.streaming_content).decode())

    def test_hg38_caches_are_isolated_and_both_assemblies_have_indexes(self):
        from django.db import connection
        from .models import Hg38ExonConservation, ExonDataset
        from .query_cache import cached_exons
        Hg38ExonConservation.objects.create(exon_id='hg38-row', name='LIVE', chrm='chrX')
        metadata = ExonDataset.objects.create(assembly='hg38', source_sha256='test-revision', row_count=1,
                                              available_fields=['exon_id', 'name', 'chrm'])
        hg19 = self.client.get('/', {'assembly': 'hg19', 'columns': ['name']})
        params = {'assembly': 'hg38', 'columns': ['name']}
        first = self.client.get('/', params)
        self.assertEqual(first.context['exons'], [('LIVE',)])
        self.assertNotEqual(first.context['exons'], hg19.context['exons'])
        self.assertIn(('chrX', 'chrX'), first.context['form'].fields['chromosome'].choices)
        with self.assertNumQueries(1):
            second = self.client.get('/', params)
        self.assertEqual(second.context['exons'], [('LIVE',)])
        with self.assertNumQueries(1):
            self.assertEqual(self.client.get('/', dict(params, results_window='1')).json()['rows'], [['LIVE']])
        # Even identical revisions/identities must never mix assemblies.
        self.assertEqual(cached_exons('hg19', 'same', 'count', {}, lambda: 19), 19)
        self.assertEqual(cached_exons('hg38', 'same', 'count', {}, lambda: 38), 38)
        Hg38ExonConservation.objects.filter(pk='hg38-row').update(name='UPDATED')
        metadata.source_sha256 = 'changed-import'
        metadata.save()
        self.assertEqual(self.client.get('/', params).context['exons'], [('UPDATED',)])
        with connection.cursor() as cursor:
            for model in (ExonConservation, Hg38ExonConservation):
                indexes = connection.introspection.get_constraints(cursor, model._meta.db_table)
                expected = {index.name for index in model._meta.indexes}
                if connection.vendor != 'postgresql':
                    expected = {name for name in expected if not name.endswith('_trgm_idx')}
                self.assertTrue(expected.issubset(indexes))
        expected_fields = [index.fields for index in ExonConservation._meta.indexes]
        expected_fields = [['ultrain_score_20pct_pm3'] if fields == ['ultra_in'] else fields for fields in expected_fields]
        self.assertEqual([index.fields for index in Hg38ExonConservation._meta.indexes], expected_fields)
