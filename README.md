
## Local development

With Docker Desktop running and `.env.dev` containing `SECRET_KEY`, start the
local PostgreSQL database and app from the repository root:

```sh
docker compose up --build
```

Open http://localhost:8000. Compose mounts the source at `/app`, waits for
PostgreSQL, runs migrations, and imports the CSV atomically on the first start.
The local Compose configuration uses the `db` service, not Render.

Run the regression tests with the app running:

```sh
docker compose exec web python manage.py test rna
```

Migration files must be committed with model changes. Existing databases created
by the old manual table-creation signal may not match the migration history. If
migration fails, inspect the schema/history before retrying; do not fake migrations
or delete a database volume to bypass the error. The importer refuses an existing
partial or different set of exon IDs instead of silently treating it as complete.

## Genome assemblies and new columns

The Genome Assembly selector routes hg19 and hg38 searches to separate tables in
the same PostgreSQL database. Local startup imports `app/data/hg19_exon_conservation.csv`
and `app/data/hg38_exon_conservation.csv`. Missing annotations are stored as NULL;
filters and column choices only appear when the source CSV provides that field.
Downloads and scrolling requests retain the selected assembly.

After changing a CSV, re-import the assembly:

```sh
docker compose exec web python manage.py import_exons --assembly hg38
```

Recognized columns added later automatically become available after re-import.
For example, `EXON TYPE`, `Exon Type`, and `exon_type` map to the same field;
`Total Exons` maps to `total_exon`. The importer ignores case, spaces, and
punctuation and uses explicit equivalent names in `app/rna/datasets.py`.
Unrecognized columns are reported with suggestions where possible, not silently
assigned by fuzzy matching. Add a confirmed alias there for an unfamiliar name;
a genuinely new metric also needs a model field, migration, and column label.
Conflicting duplicate aliases cause the import to roll back.

Changed CSVs update existing records and availability atomically; unchanged files
are skipped using a checksum. The exon ID set must match an existing dataset to
prevent accidental assembly replacement or partial imports. Existing data is not
deleted. When a previously available column is removed, its values are cleared
and its controls disappear after re-import.

The hg38 `ultrain_score_20pct_pm3` is kept separate from hg19 `ultra_in` because
their methods have not been confirmed equivalent. Coordinate values are preserved
as supplied; no genome conversion or coordinate-system inference is performed.

## Search performance

Migrations `0006` and `0007` add matching hg19 and hg38 indexes for chromosome/result ordering, genomic
coordinates, exon type, length, total exon count, splice scores, PhyloP, and Ultra
In Score. PostgreSQL also gets a `pg_trgm` GIN index on `UPPER(name)` matching
Django's case-insensitive gene-name substring queries. hg38 uses its own Ultra
In Score field (`ultrain_score_20pct_pm3`). Indexes for optional columns are ready
if those annotations are added later; unavailable controls remain hidden.
The local PostgreSQL role can create the extension; other deployments need
permission to create `pg_trgm` or an administrator to install it first.

A bounded process-local cache stores per-assembly dropdown choices, counts, and 200-row
result windows for five minutes (maximum 128 entries). Keys include the source
CSV fingerprint, assembly, query, selected columns, and offset as applicable. Each request
reads the current fingerprint from SQL, so a changed CSV import invalidates older
entries across workers without requiring Redis. Full downloads bypass
this cache. Direct SQL/admin edits can remain cached for up to five minutes.

With the app running, apply indexes and run the PostgreSQL tests:

```sh
docker compose exec web python manage.py migrate
docker compose exec web python manage.py test rna
```

Alternatively, stop the foreground Compose session and run `docker compose up
--build`; startup applies migrations automatically. Initial index creation can
briefly block writes to the table being indexed. Restarting a worker clears its local cache.
