#!/usr/bin/env python3
"""
Example: Batch Download with Progress Tracking
Downloads multiple files with rate limiting and progress reporting
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from robust_web_fetcher import RobustWebFetcher, DownloadStatus, filename_from_url

def main():
    # URLs to download
    urls = [
        "https://www.dni.gov/files/ODNI/documents/assessments/Prelimary-Assessment-UAP-20210625.pdf",
        "https://www.dni.gov/files/ODNI/documents/assessments/Unclassified-2022-Annual-Report-UAP.pdf",
        "https://arxiv.org/pdf/2403.08155",
    ]

    output_dir = "batch_downloads"
    os.makedirs(output_dir, exist_ok=True)

    # Create fetcher with conservative rate limiting
    fetcher = RobustWebFetcher(rate_limit_delay=3.0)

    print(f"\n{'='*70}")
    print(f"Batch Download - {len(urls)} files")
    print(f"Output: {output_dir}/")
    print(f"{'='*70}\n")

    results = []

    for i, url in enumerate(urls, 1):
        filename = filename_from_url(url, preferred_ext=".pdf")
        output_path = os.path.join(output_dir, filename)

        print(f"[{i}/{len(urls)}] {filename}")
        print(f"  URL: {url}")

        result = fetcher.fetch(
            url=url,
            output_path=output_path,
            try_mirrors=True,
            try_wayback=True
        )

        if result.status in (DownloadStatus.SUCCESS, DownloadStatus.WAYBACK_SUCCESS):
            file_size = os.path.getsize(result.local_path) / 1024 / 1024
            print(f"  ✓ Success ({file_size:.2f} MB, {len(result.attempted_urls)} attempts)\n")
            results.append(True)
        else:
            print(f"  ✗ Failed: {result.error_msg}\n")
            results.append(False)

    # Summary
    success_count = sum(results)
    print(f"{'='*70}")
    print(f"Complete: {success_count}/{len(urls)} successful")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
