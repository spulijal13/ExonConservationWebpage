# Exon CSV columns

Copy of [app/data/README.md](../app/data/README.md). When changing this guide, update both copies.

## Import rules

- Required in every row: `exon_id`, `chrm`, `start_position`, `end_position`, `strand`.
- IDs must be unique. Updates must contain the same IDs as the existing assembly.
- Use blank cells or `NA` for missing annotations; zero is a measured value.
- Coordinates are stored as supplied. No coordinate conversion or hg19/hg38 liftover occurs.
- Keep hg19 `ultra_in` separate from hg38 `ultrain_score_20pct_pm3`; their methods
  have not been confirmed equivalent.
- Keep standard names below. Confirm meaning before adding an alias in `rna/datasets.py`.
  Conflicting aliases fail the import; unrecognized columns are reported and ignored.
- Controls depend on recognized column headers, even if all values in a column are missing.
  Removing a column on re-import clears its previous values.

The tables describe **source CSV columns**, not just fields available in the app.
Only model fields in `rna/models.py` are imported; source-only fields such as
`row_id`, `transcript_start`, and `source_*` are not searchable or downloadable.
Do not change values or column order when only standardizing headers.

**Indexed** means PostgreSQL has a structure to speed searches. Combined indexes
cover chromosome + ID, chromosome + coordinates, and exon type + ID. Gene names
use trigram substring matching. Optional hg38 exon type/count indexes are already present.

See [run/import commands](../README.md) and [adding a metric](MAINTENANCE.md#add-a-column-or-filter).

## hg19_exon_conservation.csv

| Standardized column | Indexed | Meaning |
| --- | --- | --- |
| `exon_id` | Yes | Unique exon ID. |
| `name` | Yes | Gene name. |
| `chrm` | Yes | Chromosome, e.g. `chr1`. |
| `start_position` | Yes | Exon start coordinate. |
| `end_position` | Yes | Exon end coordinate. |
| `exon_type` | Yes | First, internal, last, or single exon. |
| `length` | Yes | Exon length in bases. |
| `total_exon` | Yes | Total exons in the source transcript. |
| `ss_score3` | Yes | 3′ splice-site score. |
| `ss_score5` | Yes | 5′ splice-site score. |
| `phylo_p` | Yes | Exon PhyloP score. |
| `ultra_in` | Yes | hg19 Ultra In score. |
| `row_id` | — | Original row index. |
| `info` | — | Source transcript/exon annotation. |
| `strand` | — | `+` or `-`. |
| `exon_number` | — | Exon rank and total, e.g. `7_8`. |
| `previous_intron` | — | Preceding intron length. |
| `next_intron` | — | Following intron length. |
| `phastcons_100` | — | PhastCons100 conservation score. |
| `prime3` | — | Source 3′ annotation flag. |
| `prime5` | — | Source 5′ annotation flag. |
| `cassette` | — | Cassette-exon flag. |
| `const` | — | Constitutive-exon flag. |
| `similarity_score` | — | Source similarity score. |
| `gene_phylo_p` | — | Gene-level PhyloP score. |
| `genes_ultra` | — | Gene-level Ultra annotation. |

## hg38_exon_conservation.csv

| Standardized column | Indexed | Meaning |
| --- | --- | --- |
| `exon_id` | Yes | Unique Ensembl exon ID. |
| `name` | Yes | Gene name. |
| `chrm` | Yes | Chromosome, e.g. `chr1`. |
| `start_position` | Yes | Exon start coordinate. |
| `end_position` | Yes | Exon end coordinate. |
| `length` | Yes | Exon length in bases. |
| `ss_score3` | Yes | 3′ splice-site score. |
| `ss_score5` | Yes | 5′ splice-site score. |
| `phylo_p` | Yes | Exon PhyloP score. |
| `ultrain_score_20pct_pm3` | Yes | hg38 Ultra In score; keep separate from hg19 `ultra_in`. |
| `row_id` | — | Original row index. |
| `gene_stable_id` | — | Ensembl gene ID. |
| `gene_type` | — | Gene classification. |
| `strand` | — | `+` or `-`. |
| `exon_number` | — | Exon rank in the source transcript. |
| `transcript_start` | — | Transcript start coordinate. |
| `transcript_end` | — | Transcript end coordinate. |
| `cds_start` | — | Source CDS start. |
| `cds_end` | — | Source CDS end. |
| `ss_start3` | — | 3′ splice-site interval start. |
| `ss_end3` | — | 3′ splice-site interval end. |
| `ss_start5` | — | 5′ splice-site interval start. |
| `ss_end5` | — | 5′ splice-site interval end. |
| `ss_sequence3` | — | 3′ splice-site sequence. |
| `ss_sequence5` | — | 5′ splice-site sequence. |
| `chromosome_raw` | — | Original chromosome notation. |
| `strand_raw` | — | Original strand notation (`1` or `-1`). |
| `coord_key_direct` | — | Source chromosome/coordinate/strand key. |
| `human_coord` | — | Source human coordinate string. |
| `species_tested_with_gtf` | — | Number of species tested using GTF annotations. |
| `species_passing_20pct` | — | Species count passing the 20% criterion. |
| `species_passing_pm3` | — | Species count passing the ±3 bp criterion. |
| `species_passing_ultrain` | — | List of species passing the combined criterion. |
| `ultrain_panel_size` | — | Number of species in the panel. |
| `ultrain_normalized` | — | Normalized Ultra In score. |
| `ultrain_evaluation_coverage` | — | Coverage of the species evaluation. |
| `source_gene_stable_id` | — | Retained original gene ID column. |
| `source_name` | — | Retained original gene-name column. |
| `source_gene_type` | — | Retained original gene-type column. |
| `source_chromosome` | — | Retained original chromosome/scaffold column. |
| `source_exon_id` | — | Retained original exon ID column. |
| `source_start_position` | — | Retained original exon-start column. |
| `source_end_position` | — | Retained original exon-end column. |
| `source_exon_number` | — | Retained original exon-rank column. |
| `source_strand` | — | Retained original strand column. |
| `source_length` | — | Retained original exon-length column. |
