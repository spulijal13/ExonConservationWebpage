"""Optional hg19 UCSC alignment helper; independent of the exon database app."""

import requests
from bs4 import BeautifulSoup

def fetch_ucsc_multiz_maf(chrom, start, end, output_file="downloaded_alignment.maf"):
    url = "https://genome.ucsc.edu/cgi-bin/hgTables"
    
    region = f"{chrom}:{start}-{end}"
    form_data = {
        "clade": "mammal",
        "org": "Human",
        "db": "hg19",
        "hgta_group": "compGeno",
        "hgta_track": "cons100way",
        "hgta_table": "multiz100way",
        "hgta_regionType": "range",
        "position": region,
        "hgta_outputType": "maf",
        "hgta_outFileName": "",
        "boolshad.hgta_printAllFields": "on",
        "hgta_doPrint": "get output",
        "hgta_compressType": "none"
    }

    print(f"Requesting MAF for {region} from UCSC Table Browser...")
    session = requests.Session()
    response = session.post(url, data=form_data)

    soup = BeautifulSoup(response.text, "html.parser")
    pre_tag = soup.find("pre")
    text = soup.get_text()
    print(text)
    
    if pre_tag:
        maf_text = pre_tag.get_text()
        with open(output_file, "w") as f:
            f.write(maf_text)
        print(f"MAF data saved to {output_file}")
        return maf_text
    else:
        print("No MAF data found or invalid position.")
        return None

if __name__ == "__main__":
    maf_data = fetch_ucsc_multiz_maf("chr15", 67500898, 67500998)