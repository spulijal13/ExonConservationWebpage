# Exon conservation database

A Hertel Lab tool for searching exon annotations in **hg19** and **hg38**.
Filter by gene, coordinates, or scores; choose columns; download all matches.
The app uses Django (Python) and PostgreSQL (the database), packaged with Docker.

## Run locally

1. Start Docker Desktop.
2. In the repository root, create `.env.dev` with `SECRET_KEY=<your-random-key>`.
   Generate a key with `python3 -c 'import secrets; print(secrets.token_urlsafe(50))'`.
   Keep this file private; do not commit it.
3. From the repository root, run:

```sh
docker compose up --build
```

Open [localhost:8000](http://localhost:8000). First startup may take time:
Docker starts the database, applies schema updates, imports both CSVs, and collects
CSS/JavaScript. Unchanged datasets are skipped on later starts.

Stop with `Ctrl+C` or `docker compose down`. Data stays in Docker's database volume.
**Do not use `down -v` unless you intend to delete the database.**

## Search and download

- Select an assembly, then select **Load assembly**.
- Enter filters and select **Search**. Blank filters include all records.
- Gene search matches part of a name, ignoring case: `MARCHF1` also matches `MARCHF10`.
- Coordinate filters require exon start ≥ entered start and exon end ≤ entered end.
  They find contained exons, not every overlapping exon.
- Scroll or use **Go to result**. Only 200 rows are loaded at once.
- Downloads contain **all matching rows** and the selected columns. CSV and TXT
  both use comma-separated values; blank cells represent missing annotations.

## Update annotations

Keep a copy of the original CSV. Replace the relevant file in `app/data/`, then run:

```sh
docker compose exec web python manage.py import_exons --assembly hg38
```

Use `hg19` for the other assembly. Existing exon IDs must match exactly; adding or
removing IDs needs a planned dataset replacement. An import either completes or
rolls back entirely. Removing an annotation column clears its stored values.

See the [data guide](app/data/README.md) for columns, missing values, and score caveats.

## Check or troubleshoot

```sh
docker compose exec web python manage.py test rna
docker compose logs --tail=100 web
```

Tests use a separate temporary database. If startup fails, read the first error in
the logs. Do not delete data or bypass migrations to make an error disappear.

For code changes, new metrics, deployment, and common errors, see the
[maintenance guide](docs/MAINTENANCE.md).

## Lab server deployment

For Apache hosting at `/exons/`, use the [server deployment guide](docs/DEPLOYMENT.md)
and templates in `deploy/`. The runtime is pinned to Django 5.2 LTS and a complete
dependency set. Copy `.env.dev.example` for local setup; never commit real secrets.
