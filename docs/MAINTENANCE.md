# Maintenance guide

For the next student maintaining this tool. Run commands from the repository root.
Start with the [README](../README.md) and [data guide](DATA.md).

## Where things live

| File under `app/` | Purpose |
| --- | --- |
| `data/*_exon_conservation.csv` | Input annotations; not queried directly by the website. |
| `rna/management/commands/import_exons.py` | Validates CSVs and updates the database in one transaction (all or nothing). |
| `rna/models.py` | Database columns: shared annotations, separate assembly tables, import metadata. |
| `rna/migrations/` | Versioned instructions for changing the database structure. Keep existing files. |
| `rna/datasets.py` | Assembly routing and accepted alternative CSV column names. |
| `rna/forms.py` | Filter types, validation, column labels, and available controls. |
| `rna/search.py` | Translates validated filters into database queries. |
| `rna/views.py` | Returns the page, a window of rows, or a download. |
| `rna/exports.py` | Writes downloads incrementally to avoid loading all rows into memory. |
| `rna/query_cache.py` | Temporarily reuses dropdown choices, counts, and result windows. |
| `rna/templates/build.html` | Search form and results table. |
| `templates/` | Shared page layout and About text. |
| `static/javascript/main.js` | Loads visible table rows as the user scrolls. |
| `static/css/style.css` | Layout, colors, keyboard focus, and mobile styles. |
| `rna/tests.py` | Regression checks using small synthetic datasets. |
| `rna/admin.py`, `rna/resource.py` | hg19 admin interface and its export fields. |
| `exon/settings.py`, `exon/urls.py` | Configuration and URL routing. |
| `manage.py`, `exon/wsgi.py`, `exon/asgi.py` | Django command and server entry points. |
| `prepare.sh`, `entrypoint*.sh` | Database preparation, imports, and server startup. |
| `dockerfile`, `Dockerfile.prod`, `requirements.txt` | Python environment and web dependencies. |

Flow: **CSV → import → PostgreSQL → validated search → table/download**.
`ExonDataset` records which columns were imported, their source names, row count,
and SHA-256 checksum (a fingerprint of the CSV contents).

## Make a change

1. Work on a Git branch. Keep data changes separate from interface changes.
2. Edit the source under `app/`; local Docker mounts it directly. Rebuild after
   changing dependencies or Docker files.
3. Run `docker compose exec web python manage.py test rna` against PostgreSQL.
4. Check both assemblies in the browser: filters, columns, invalid input, row jumps,
   and CSV/TXT downloads. Check keyboard access and a narrow browser window.
5. Commit code, relevant migrations, and documentation together.

SQLite tests are a useful quick check, but do not verify PostgreSQL indexes.
Keep visible labels, logical headings, focus outlines, error messages, and the skip
link. Table row height must stay consistent: scrolling calculates positions from it.

## Add a column or filter

- **Another name for an existing metric:** confirm scientific equivalence, then add
  the name to `ALIASES` in `datasets.py`. Case, spaces, and punctuation are already ignored.
- **A new metric:** add a nullable field to the appropriate model and a label in
  `COLUMN_CHOICES` in `forms.py`. Add a filter there and in `search.py` only if needed.
- Generate and apply the schema change:

```sh
docker compose exec web python manage.py makemigrations rna
docker compose exec web python manage.py migrate
```

Commit the generated migration. Update the CSV, re-import, document the metric,
and test missing values, zero, and each supported comparison.
Changing alias/model code alone does not change the CSV checksum: an unchanged
file may be skipped. Plan a reviewed re-import strategy when changing import logic;
do not delete metadata or modify scientific values just to force a reload.

## Performance and data safety

- Results are ordered by exon ID. The browser holds at most four result windows.
- Each Python worker caches at most 128 entries for five minutes. Every request
  reads the dataset fingerprint; a changed import makes old cache keys obsolete.
  Direct admin/SQL edits can remain cached for five minutes. Downloads bypass this cache.
- Migrations `0006`/`0007` add search indexes. Gene substring search uses PostgreSQL
  `pg_trgm` (trigram matching); its extension needs database permission to install.
- Imports write batches of 1,000 rows but keep the whole operation in one transaction.
  Duplicate IDs, conflicting aliases, or a changed ID set roll back the operation.
- Back up the database and source CSVs before a dataset replacement or schema change.
  An unchanged-file skip checks the checksum and row count, not every stored value.

## Common problems

| Symptom | Check |
| --- | --- |
| App does not start | `docker compose logs --tail=100 web db`; check Docker, `.env.dev`, and port 8000. |
| Filter/column missing | It must exist in the model, form configuration, and imported CSV metadata. |
| “Ignored column” | Confirm the name and meaning before adding an alias; suggestions are not automatic mappings. |
| “Incomplete or different” dataset | Compare exon IDs with the existing assembly; do not delete the database to bypass this check. |
| Migration failure | Inspect `python manage.py showmigrations` inside the container and the database schema. Do not use `--fake` blindly. |
| Old annotations after an edit | Re-import the changed CSV. Direct database edits may remain cached for five minutes. |

## Production

`docker-compose.prod.yml` uses Gunicorn instead of Django's development server.
Set `.env.prod`: `SECRET_KEY`, `DEBUG=false`, `DJANGO_ALLOWED_HOSTS` (comma-separated
hostnames), `SQL_HOST=db`, `SQL_PORT=5432`, `SQL_DATABASE`, `SQL_USER`, `SQL_PASSWORD`.
Set matching `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` in `.env.prod.db`.
Keep all environment files private; local development credentials are not production credentials.

```sh
docker compose -f docker-compose.prod.yml up --build
```

Startup waits for the database and runs `prepare.sh`: migrations, both imports,
and static collection. With multiple web replicas, run `sh prepare.sh` once in an
app container as a release job and set `PREPARE_ON_START=0` for the web services.
Arrange HTTPS and serve `STATIC_ROOT` through the hosting platform/reverse proxy;
Gunicorn does not serve CSS/JavaScript itself. Index creation can block writes,
so schedule schema changes appropriately.

Dependency versions are in `app/requirements.txt`; some are unpinned. For an upgrade,
record the resolved versions and rerun PostgreSQL tests and browser checks before deployment.

## Optional UCSC utility

`app/data/multiz.py` is separate from the website and importer. It requests an hg19
alignment from UCSC and looks for a `<pre>` block in the returned HTML. It depends
on UCSC's page format and is not covered by the web regression tests.
Install `app/data/requirements.txt` in your Python environment. Review the example
coordinates and output filename before running; the script can overwrite that file.
