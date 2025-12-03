## Exon Conservation Webpage

A searchable web application for exploring exon-level conservation, splice site scores, intron context, and phylogenetic metrics across multiple genes and chromosomes.

This project is built with Django, PostgreSQL, and Docker, and is designed to make large genomic tables easy to filter and browse through a simple web interface.

⸻
## Live Site

The app is deployed on Render and available here:

👉 https://exonconservationwebpage-1.onrender.com
⸻

## 🔍 What you can do on the site

You can search exons using many biological filters, such as:
	•	Chromosome
	•	Gene name
	•	Genomic start / end
	•	Exon number and total exons
	•	Exon type (first, internal, last)
	•	Splice site 3′ / 5′ scores
	•	PhastCons100 conservation values
	•	Ultra-conserved region flags
	•	PhyloP scores
	•	Intron lengths and other context features

The results load quickly and show the matching exon rows in a clean table.

⸻

## 🧬 Data summary

The dataset includes fields such as:
	•	exon_id
	•	gene name
	•	chromosome
	•	start / end positions
	•	strand
	•	exon length
	•	exon number
	•	total exon count
	•	splice site strengths
	•	conservation scores (PhastCons100, PhyloP)
	•	ultra-conserved flags
	•	intron lengths before and after the exon

The app imports this data into a PostgreSQL table on first run.

⸻

## ⚙️ Tech stack

This project uses:
	•	Django 4
	•	PostgreSQL
	•	Docker / Docker Compose
	•	Gunicorn (for production)
	•	Whitenoise (to serve static files)
	•	Render (for deployment)

⸻
## 🤝 Contributing

If you want to add more filters, new data fields, or front end improvements, feel free to open a pull request.

⸻

## 📜 License

MIT License.

