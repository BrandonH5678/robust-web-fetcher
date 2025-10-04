# Robust Web Fetcher

> Multi-tactic download library for stubborn sites, 403 errors, and unreliable sources

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Python library that handles difficult web downloads with automatic fallback strategies, mirror rotation, and Wayback Machine integration.

## 🎯 Features

- **Multi-Engine Cascade**: Automatically tries requests → curl → wget
- **First-Party Mirrors**: Auto-rotates to known mirrors (ODNI/DoD/AARO, NASA, arXiv)
- **Wayback Fallback**: Retrieves from Internet Archive when direct download fails
- **HTML → PDF**: Converts web pages using wkhtmltopdf, Playwright, or WeasyPrint
- **Rate Limiting**: Per-domain throttling to respect server limits
- **Session Persistence**: Maintains cookies and connections across requests
- **Comprehensive Logging**: Detailed download attempts and debugging info

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/BrandonH5678/robust-web-fetcher.git
cd robust-web-fetcher

# Install dependencies
pip install -r requirements.txt

# Optional: Install HTML→PDF conversion tools
sudo apt install wkhtmltopdf  # Linux
brew install wkhtmltopdf      # macOS
```

### Basic Usage

```python
from robust_web_fetcher import RobustWebFetcher

# Create fetcher instance
fetcher = RobustWebFetcher()

# Download with all tactics enabled
result = fetcher.fetch(
    url="https://www.dni.gov/files/report.pdf",
    output_path="report.pdf",
    try_mirrors=True,   # Try known mirrors on failure
    try_wayback=True,   # Fall back to Wayback Machine
    timeout=90
)

if result.status.name.endswith("SUCCESS"):
    print(f"✓ Downloaded: {result.local_path}")
else:
    print(f"✗ Failed: {result.error_msg}")
    if result.wayback_url:
        print(f"Manual fallback: {result.wayback_url}")
```

## 📖 Common Scenarios

### Government PDFs (ODNI, DoD, NASA)

```python
fetcher = RobustWebFetcher(rate_limit_delay=2.0)

# Automatically tries dni.gov → defense.gov → aaro.mil mirrors
result = fetcher.fetch(
    "https://www.dni.gov/files/ODNI/documents/report.pdf",
    "odni_report.pdf",
    try_mirrors=True,
    try_wayback=True
)
```

### arXiv Papers

```python
# Handles /abs/ → /pdf/ redirect automatically
result = fetcher.fetch(
    "https://arxiv.org/abs/2502.06794",
    "paper.pdf",
    try_mirrors=True  # Also tries export.arxiv.org
)
```

### HTML to PDF Conversion

```python
# Download HTML page
result = fetcher.fetch("https://example.gov/page.html", "page.html")

# Convert to PDF (auto-detects available engine)
if result.local_path.endswith(".html"):
    fetcher.html_to_pdf(result.local_path, "page.pdf", engine="auto")
```

### Batch Downloads with Rate Limiting

```python
fetcher = RobustWebFetcher(rate_limit_delay=3.0)

urls = [
    "https://site1.gov/doc1.pdf",
    "https://site2.gov/doc2.pdf",
]

for i, url in enumerate(urls):
    result = fetcher.fetch(url, f"doc_{i}.pdf")
    # Automatically rate-limited per domain
```

## 🎓 How It Works

### Download Strategy Cascade

1. **Direct Download** (requests with session)
   - Fast, handles cookies and compression
   - Randomized user agents

2. **Fallback: curl** (if requests fails)
   - Often bypasses naive user-agent blocks
   - System-level tool, different fingerprint

3. **Fallback: wget** (if curl fails)
   - Alternative engine
   - Sometimes works when others don't

4. **Mirror Rotation** (if enabled)
   - Tries known first-party mirrors
   - ODNI ↔ DoD ↔ AARO
   - NASA ↔ science.nasa.gov ↔ ntrs.nasa.gov
   - arXiv ↔ export.arxiv.org

5. **Wayback Machine** (if enabled)
   - Queries Internet Archive API
   - Downloads most recent snapshot
   - Provides manual fallback URL

### Supported Mirror Domains

| Original Domain | Mirrors |
|----------------|---------|
| dni.gov | defense.gov, aaro.mil, intelligence.gov |
| defense.gov | dni.gov, aaro.mil |
| aaro.mil | defense.gov, dni.gov |
| nasa.gov | science.nasa.gov, ntrs.nasa.gov |
| arxiv.org | export.arxiv.org |

## 📊 API Reference

### RobustWebFetcher

```python
class RobustWebFetcher:
    def __init__(
        self,
        cache_dir: str = ".web_cache",
        rate_limit_delay: float = 1.5
    ):
        """
        Initialize fetcher

        Args:
            cache_dir: Directory for temporary files
            rate_limit_delay: Seconds between requests to same domain
        """
```

### fetch()

```python
def fetch(
    self,
    url: str,
    output_path: str,
    try_mirrors: bool = True,
    try_wayback: bool = True,
    timeout: int = 60
) -> DownloadResult:
    """
    Download file with multi-tactic strategy

    Args:
        url: URL to download
        output_path: Local path to save file
        try_mirrors: Enable first-party mirror rotation
        try_wayback: Enable Wayback Machine fallback
        timeout: Request timeout in seconds

    Returns:
        DownloadResult with status, path, and metadata
    """
```

### html_to_pdf()

```python
def html_to_pdf(
    self,
    html_path: str,
    pdf_path: str,
    engine: str = "auto"
) -> bool:
    """
    Convert HTML to PDF

    Args:
        html_path: Path to HTML file
        pdf_path: Output PDF path
        engine: "auto", "wkhtmltopdf", "playwright", or "weasyprint"

    Returns:
        True if conversion succeeded
    """
```

### DownloadResult

```python
@dataclass
class DownloadResult:
    status: DownloadStatus          # SUCCESS, FAILED_403, etc.
    local_path: Optional[str]       # Path to downloaded file
    content_type: Optional[str]     # MIME type
    source_url: str                 # Original URL
    attempted_urls: List[str]       # All URLs tried
    wayback_url: Optional[str]      # Wayback fallback URL
    error_msg: Optional[str]        # Error description
```

### DownloadStatus Enum

```python
class DownloadStatus(Enum):
    SUCCESS = "success"
    WAYBACK_SUCCESS = "wayback_success"
    FAILED_403 = "failed_403"
    FAILED_404 = "failed_404"
    FAILED_TIMEOUT = "failed_timeout"
    FAILED_NETWORK = "failed_network"
    FAILED_MIRROR = "failed_all_mirrors"
```

## 🛠️ Dependencies

### Required
- Python 3.8+
- `requests` library

### Optional (Enhanced Capabilities)
- `curl` - Fallback downloader (usually pre-installed)
- `wget` - Alternative fallback (usually pre-installed)
- `wkhtmltopdf` - HTML→PDF conversion (recommended)
- `playwright` - Modern HTML→PDF with JS support
- `weasyprint` - Pure Python HTML→PDF

## 🧪 Testing

```bash
# Run built-in test
python3 robust_web_fetcher.py

# Run interactive demo
python3 examples/demo.py

# Run example: Download UAP reading list
python3 examples/uap_reading_list.py
```

## 🔒 Security & Compliance

### ✅ Best Practices
- Respects robots.txt (manual verification recommended)
- Configurable rate limiting per domain
- Standard HTTP headers and practices
- No authentication credential handling

### ⚠️ Limitations
- Does not bypass CAPTCHAs
- Does not handle login-protected content
- Wayback retrieval may violate some sites' ToS (review case-by-case)
- Not suitable for aggressive scraping

## 📚 Examples

See the [`examples/`](examples/) directory for:
- **demo.py** - Interactive demonstration of all tactics
- **uap_reading_list.py** - Download government UAP reports
- **batch_download.py** - Batch downloading with progress tracking

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Developed as part of the Sherlock intelligence analysis system
- Built to handle difficult-to-access government and academic sources
- Inspired by the need for reliable evidence gathering

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/BrandonH5678/robust-web-fetcher/issues)
- **Documentation**: See [docs/](docs/) directory
- **Examples**: See [examples/](examples/) directory

## 🗺️ Roadmap

- [ ] Add support for FTP downloads
- [ ] Implement parallel batch downloads
- [ ] Add proxy support
- [ ] Create CLI tool
- [ ] Add progress bars for large files
- [ ] Browser automation for JavaScript-heavy sites

---

**Made with ❤️ for reliable intelligence gathering**
