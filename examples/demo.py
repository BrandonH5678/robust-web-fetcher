#!/usr/bin/env python3
"""
Robust Web Fetcher - Quick Demo
Demonstrates basic usage and all download tactics
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from robust_web_fetcher import RobustWebFetcher, DownloadStatus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Run quick demonstration"""

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║          Robust Web Fetcher - Quick Demo                    ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    # Create output directory
    import os
    os.makedirs("demo_output", exist_ok=True)

    # Initialize fetcher
    fetcher = RobustWebFetcher(rate_limit_delay=2.0)

    # Test cases
    test_urls = [
        {
            "name": "ODNI UAP Report (2021)",
            "url": "https://www.dni.gov/files/ODNI/documents/assessments/Prelimary-Assessment-UAP-20210625.pdf",
            "output": "demo_output/odni_uap_2021.pdf",
        },
        {
            "name": "arXiv Paper (abstract page)",
            "url": "https://arxiv.org/abs/2403.08155",
            "output": "demo_output/arxiv_starlink.pdf",
        },
    ]

    results = []

    for i, test in enumerate(test_urls, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(test_urls)}] {test['name']}")
        print(f"URL: {test['url']}")
        print(f"{'='*70}")

        result = fetcher.fetch(
            url=test['url'],
            output_path=test['output'],
            try_mirrors=True,
            try_wayback=True,
            timeout=90
        )

        results.append({
            "name": test['name'],
            "status": result.status,
            "path": result.local_path,
            "attempts": len(result.attempted_urls),
        })

        if result.status in (DownloadStatus.SUCCESS, DownloadStatus.WAYBACK_SUCCESS):
            print(f"✓ SUCCESS: {result.local_path}")
        else:
            print(f"✗ FAILED: {result.error_msg}")
            if result.wayback_url:
                print(f"  Wayback: {result.wayback_url}")

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    success_count = sum(1 for r in results if r['status'] in (DownloadStatus.SUCCESS, DownloadStatus.WAYBACK_SUCCESS))

    for r in results:
        status_symbol = "✓" if r['status'] in (DownloadStatus.SUCCESS, DownloadStatus.WAYBACK_SUCCESS) else "✗"
        print(f"{status_symbol} {r['name']}: {r['status'].value} ({r['attempts']} attempts)")

    print(f"\nSuccess rate: {success_count}/{len(results)}")
    print(f"Output directory: demo_output/")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo cancelled by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
