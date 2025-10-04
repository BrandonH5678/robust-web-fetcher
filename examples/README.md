# Examples

This directory contains example scripts demonstrating various uses of Robust Web Fetcher.

## Quick Demo
Basic demonstration of all download tactics:
```bash
python3 demo.py
```

## UAP Reading List
Download official government and academic UAP/UFO reports:
```bash
python3 uap_reading_list.py

# With custom output directory
OUTDIR="my_downloads" python3 uap_reading_list.py

# With HTML→PDF conversion
CONVERT_HTML_TO_PDF=1 python3 uap_reading_list.py
```

## Batch Download
Download multiple files with progress tracking:
```bash
python3 batch_download.py
```

## Custom Example
Create your own script:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add parent directory to path (for local development)
sys.path.insert(0, str(Path(__file__).parent.parent))

from robust_web_fetcher import RobustWebFetcher

# Create fetcher
fetcher = RobustWebFetcher()

# Download with all tactics
result = fetcher.fetch(
    url="https://example.gov/document.pdf",
    output_path="document.pdf",
    try_mirrors=True,
    try_wayback=True
)

if result.status.name.endswith("SUCCESS"):
    print(f"✓ Downloaded: {result.local_path}")
```

## Output

All examples create output in separate directories:
- `demo.py` → `demo_output/`
- `uap_reading_list.py` → `uap_reading_list/` (or custom via `OUTDIR`)
- `batch_download.py` → `batch_downloads/`

These directories are .gitignored and safe to delete.
