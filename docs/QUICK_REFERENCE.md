# Robust Web Fetcher - Quick Reference

## 🚀 Quick Start (Copy-Paste Ready)

### Simple Download
```python
from robust_web_fetcher import RobustWebFetcher

fetcher = RobustWebFetcher()
result = fetcher.fetch("https://site.gov/report.pdf", "output.pdf")

if result.status.name.endswith("SUCCESS"):
    print(f"Downloaded: {result.local_path}")
```

### With All Tactics Enabled
```python
result = fetcher.fetch(
    url="https://www.dni.gov/files/report.pdf",
    output_path="report.pdf",
    try_mirrors=True,    # ✓ Try dni.gov → defense.gov → aaro.mil
    try_wayback=True,    # ✓ Fall back to Wayback Machine
    timeout=90
)
```

## 📋 Common Scenarios

### Government PDFs (ODNI, DoD, NASA, AARO)
```python
from robust_web_fetcher import RobustWebFetcher, DownloadStatus

fetcher = RobustWebFetcher(rate_limit_delay=2.0)

# Auto-tries mirrors: dni.gov ↔ defense.gov ↔ aaro.mil
result = fetcher.fetch(
    "https://www.dni.gov/files/ODNI/documents/report.pdf",
    "odni_report.pdf",
    try_mirrors=True,
    try_wayback=True
)
```

### arXiv Papers (handles /abs/ → /pdf/ redirect)
```python
# Works with both abstract and PDF URLs
result = fetcher.fetch(
    "https://arxiv.org/abs/2502.06794",  # Abstract page
    "paper.pdf",
    try_mirrors=True  # Also tries export.arxiv.org
)
```

### HTML → PDF Conversion
```python
# Download HTML
result = fetcher.fetch("https://site.gov/page.html", "page.html")

# Convert to PDF (auto-detects wkhtmltopdf/playwright/weasyprint)
if result.local_path.endswith(".html"):
    fetcher.html_to_pdf(result.local_path, "page.pdf", engine="auto")
```

### Batch Downloads (Rate Limited)
```python
fetcher = RobustWebFetcher(rate_limit_delay=3.0)  # 3s between requests

urls = ["https://site1.gov/doc.pdf", "https://site2.gov/doc.pdf"]
for url in urls:
    result = fetcher.fetch(url, f"{i}.pdf")
    # Automatically rate-limited per domain
```

## 🎯 Advanced Tactics

### 1. Mirror Rotation (First-Party)
**When:** Government/academic sites with known mirrors
**How:** Set `try_mirrors=True`
**Domains:** dni.gov, defense.gov, aaro.mil, nasa.gov, arxiv.org

### 2. Wayback Fallback
**When:** Site is down or content removed
**How:** Set `try_wayback=True`
**Result:** Downloads most recent snapshot or provides manual URL

### 3. Multi-Engine Cascade
**Order:** requests → curl → wget
**Automatic:** No config needed
**Why:** Different engines bypass different blocks

### 4. arXiv Special Handling
**Handles:**
- `/abs/` → `/pdf/` redirect
- Trailing `.pdf` addition
- `export.arxiv.org` mirror

### 5. Rate Limiting
**Per-domain:** Respects individual domain delays
**Config:** `RobustWebFetcher(rate_limit_delay=2.0)`
**Default:** 1.5 seconds

### 6. Session Persistence
**Automatic:** Cookies and connections maintained
**Benefit:** Faster subsequent requests
**Scope:** Per fetcher instance

## 📊 Status Codes

| Status | Meaning |
|--------|---------|
| `SUCCESS` | Downloaded directly |
| `WAYBACK_SUCCESS` | Retrieved from archive |
| `FAILED_403` | Forbidden (all tactics failed) |
| `FAILED_404` | Not found |
| `FAILED_TIMEOUT` | Request timeout |
| `FAILED_NETWORK` | Network error |
| `FAILED_MIRROR` | All mirrors exhausted |

## 🛠️ Installation

### Required
```bash
pip install requests
```

### Optional (Recommended)
```bash
# Multi-engine support (usually pre-installed)
sudo apt install curl wget

# HTML→PDF (choose one)
sudo apt install wkhtmltopdf              # Fast, good rendering
pip install playwright && playwright install chromium  # Modern, handles JS
pip install weasyprint                    # Pure Python
```

## 🔍 Troubleshooting

### All Downloads Return 403
```python
# Increase rate limit delay
fetcher = RobustWebFetcher(rate_limit_delay=5.0)

# Check manual Wayback URL
if result.wayback_url:
    print(f"Manual: {result.wayback_url}")
```

### HTML→PDF Fails
```bash
# Install conversion engine
sudo apt install wkhtmltopdf
```

### Import Error
```python
# Ensure robust_web_fetcher.py is in Python path
import sys
sys.path.insert(0, "/home/johnny5/Sherlock")
from robust_web_fetcher import RobustWebFetcher
```

## 📚 Examples

See `/home/johnny5/Sherlock/examples/web_fetcher_tactics_demo.py` for interactive demonstrations.

## 🔗 Integration

### Sherlock
```python
from robust_web_fetcher import RobustWebFetcher
fetcher = RobustWebFetcher(cache_dir="evidence_cache")
```

### J5A
```python
fetcher = RobustWebFetcher(rate_limit_delay=3.0)  # Conservative for monitoring
```

### Squirt
```python
fetcher = RobustWebFetcher()  # Standard config for business intelligence
```

## 📖 Full Documentation

- **Integration Guide:** `ROBUST_WEB_FETCHER_INTEGRATION.md`
- **Source Code:** `robust_web_fetcher.py`
- **Demo Script:** `examples/web_fetcher_tactics_demo.py`
