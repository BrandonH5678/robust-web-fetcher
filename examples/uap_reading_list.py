#!/usr/bin/env python3
"""
Example: Download UAP/UFO Reading List
Downloads official government and academic UAP reports
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from robust_web_fetcher import RobustWebFetcher, DownloadStatus, filename_from_url

OUTDIR = os.environ.get("OUTDIR", "uap_reading_list")
CONVERT_HTML = os.environ.get("CONVERT_HTML_TO_PDF", "0") == "1"

DOCS = [
    {
        "title": "FY2024 Consolidated Annual Report on UAP (Unclassified)",
        "url": "https://www.dni.gov/index.php/newsroom/reports-publications/reports-publications-2024/4020-uap-2024",
    },
    {
        "title": "AARO Historical Record Report, Volume I (Mar 8, 2024)",
        "url": "https://media.defense.gov/2024/Mar/08/2003409233/-1/-1/0/DOPSR-CLEARED-508-COMPLIANT-HRRV1-08-MAR-2024-FINAL.PDF",
    },
    {
        "title": "NASA UAP Independent Study Team – Final Report (2023)",
        "url": "https://science.nasa.gov/wp-content/uploads/2023/09/uap-independent-study-team-final-report.pdf",
    },
    {
        "title": "ODNI Preliminary Assessment of UAP (2021)",
        "url": "https://www.dni.gov/files/ODNI/documents/assessments/Prelimary-Assessment-UAP-20210625.pdf",
    },
    {
        "title": "2022 Annual Report on UAP (ODNI)",
        "url": "https://www.dni.gov/files/ODNI/documents/assessments/Unclassified-2022-Annual-Report-UAP.pdf",
    },
]

def main():
    os.makedirs(OUTDIR, exist_ok=True)

    fetcher = RobustWebFetcher(rate_limit_delay=2.0)
    manifest = []

    print(f"\n{'='*70}")
    print("UAP Reading List Downloader")
    print(f"{'='*70}\n")

    for i, doc in enumerate(DOCS, 1):
        print(f"[{i}/{len(DOCS)}] {doc['title']}")

        is_pdf = doc['url'].lower().endswith('.pdf')
        ext = '.pdf' if is_pdf else '.html'
        filename = filename_from_url(doc['url'], preferred_ext=ext)
        output_path = os.path.join(OUTDIR, filename)

        result = fetcher.fetch(
            url=doc['url'],
            output_path=output_path,
            try_mirrors=True,
            try_wayback=True,
            timeout=90
        )

        if result.status in (DownloadStatus.SUCCESS, DownloadStatus.WAYBACK_SUCCESS):
            print(f"  ✓ Downloaded: {result.local_path}\n")

            # Convert HTML to PDF if requested
            if CONVERT_HTML and result.local_path.endswith('.html'):
                pdf_path = result.local_path.replace('.html', '.pdf')
                if fetcher.html_to_pdf(result.local_path, pdf_path):
                    print(f"  ✓ Converted to PDF: {pdf_path}\n")
                    result.local_path = pdf_path

            manifest.append({
                "title": doc['title'],
                "source_url": doc['url'],
                "local_path": result.local_path,
                "status": "OK",
                "type": "pdf" if result.local_path.endswith('.pdf') else "html",
            })
        else:
            print(f"  ✗ Failed: {result.error_msg}")
            if result.wayback_url:
                print(f"  Wayback: {result.wayback_url}\n")

            manifest.append({
                "title": doc['title'],
                "source_url": doc['url'],
                "local_path": None,
                "status": "FAILED",
                "wayback": result.wayback_url,
            })

    # Save manifest
    manifest_path = os.path.join(OUTDIR, "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    # Summary
    success = sum(1 for m in manifest if m['status'] == 'OK')
    print(f"\n{'='*70}")
    print(f"Downloaded: {success}/{len(DOCS)}")
    print(f"Output: {OUTDIR}/")
    print(f"Manifest: {manifest_path}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
