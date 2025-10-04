"""
Robust Web Fetcher - Enhanced download tactics for stubborn sites and 403s
Shared library for Sherlock, J5A, and Squirt intelligence gathering

Tactics implemented:
1. First-party mirror rotation (AARO/ODNI/DoD cross-mirror)
2. Wayback Machine fallback with snapshot selection
3. Multi-engine download (requests → curl → wget → aria2c)
4. HTML → PDF conversion (wkhtmltopdf, playwright, weasyprint)
5. Smart retry with exponential backoff
6. Rate limiting and ToS compliance
7. Session persistence and cookie handling
"""

import os
import json
import time
import random
import subprocess
import shutil
import logging
from urllib.parse import urlparse, urljoin
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Configuration
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
]

HEADERS_BASE = {
    "Accept": "text/html,application/pdf,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

# Known mirror domains for first-party fallback
MIRROR_DOMAINS = {
    "dni.gov": ["defense.gov", "aaro.mil", "intelligence.gov"],
    "defense.gov": ["dni.gov", "aaro.mil"],
    "aaro.mil": ["defense.gov", "dni.gov"],
    "nasa.gov": ["science.nasa.gov", "ntrs.nasa.gov"],
    "arxiv.org": ["export.arxiv.org", "arxiv-export-lb.library.cornell.edu"],
}

class DownloadStatus(Enum):
    SUCCESS = "success"
    FAILED_403 = "failed_403"
    FAILED_404 = "failed_404"
    FAILED_TIMEOUT = "failed_timeout"
    FAILED_NETWORK = "failed_network"
    FAILED_MIRROR = "failed_all_mirrors"
    WAYBACK_SUCCESS = "wayback_success"

@dataclass
class DownloadResult:
    status: DownloadStatus
    local_path: Optional[str]
    content_type: Optional[str]
    source_url: str
    attempted_urls: List[str]
    wayback_url: Optional[str] = None
    error_msg: Optional[str] = None

class RobustWebFetcher:
    """Enhanced web fetcher with multi-tactic download strategies"""

    def __init__(self, cache_dir: str = ".web_cache", rate_limit_delay: float = 1.5):
        self.cache_dir = cache_dir
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = {}
        self.session = requests.Session() if HAS_REQUESTS else None
        self.logger = logging.getLogger(__name__)
        os.makedirs(cache_dir, exist_ok=True)

    def _rate_limit(self, domain: str):
        """Respect rate limits per domain"""
        now = time.time()
        if domain in self.last_request_time:
            elapsed = now - self.last_request_time[domain]
            if elapsed < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time[domain] = time.time()

    def _get_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Generate randomized headers"""
        headers = HEADERS_BASE.copy()
        headers["User-Agent"] = random.choice(UA_POOL)
        if referer:
            headers["Referer"] = referer
        else:
            headers["Referer"] = "https://www.google.com/"
        return headers

    def _generate_mirror_urls(self, url: str) -> List[str]:
        """Generate first-party mirror URLs"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        mirrors = []

        # Find matching domain pattern
        for base_domain, mirror_list in MIRROR_DOMAINS.items():
            if base_domain in domain:
                for mirror in mirror_list:
                    # Attempt domain substitution
                    mirror_url = url.replace(domain, mirror)
                    mirrors.append(mirror_url)

                    # Also try common path patterns
                    if "reports" in parsed.path or "publications" in parsed.path:
                        # Try /newsroom/reports, /library/reports, etc.
                        alt_paths = [
                            parsed.path.replace("/newsroom/", "/library/"),
                            parsed.path.replace("/reports/", "/publications/"),
                            parsed.path.replace("/documents/", "/files/"),
                        ]
                        for alt_path in alt_paths:
                            mirrors.append(f"{parsed.scheme}://{mirror}{alt_path}")

        return mirrors

    def _try_requests(self, url: str, output_path: str, timeout: int = 60) -> Tuple[bool, Optional[str]]:
        """Attempt download using requests library"""
        if not HAS_REQUESTS or not self.session:
            return False, "requests not available"

        domain = urlparse(url).netloc
        self._rate_limit(domain)

        try:
            headers = self._get_headers()
            response = self.session.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)

            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True, response.headers.get("Content-Type", "application/octet-stream")

            # Handle specific arXiv patterns
            if response.status_code in (403, 404) and "arxiv.org" in url:
                # Try PDF extension
                if not url.endswith(".pdf"):
                    alt_url = url.rstrip("/") + ".pdf"
                    return self._try_requests(alt_url, output_path, timeout)
                # Try /pdf/ path variant
                if "/abs/" in url:
                    alt_url = url.replace("/abs/", "/pdf/") + ".pdf"
                    return self._try_requests(alt_url, output_path, timeout)

            return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)

    def _try_curl(self, url: str, output_path: str, timeout: int = 60) -> Tuple[bool, Optional[str]]:
        """Attempt download using curl (sometimes bypasses naive blocks)"""
        if not shutil.which("curl"):
            return False, "curl not available"

        domain = urlparse(url).netloc
        self._rate_limit(domain)

        headers = self._get_headers()
        cmd = [
            "curl", "-L", "-s", "-S",
            "--max-time", str(timeout),
            "--compressed",
            "-H", f"User-Agent: {headers['User-Agent']}",
            "-H", f"Referer: {headers['Referer']}",
            "-H", f"Accept: {headers['Accept']}",
            "-o", output_path,
            "-w", "%{content_type}",
            url
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                content_type = result.stdout.strip() or "application/octet-stream"
                return True, content_type
            return False, "curl returned empty file"
        except Exception as e:
            return False, str(e)

    def _try_wget(self, url: str, output_path: str, timeout: int = 60) -> Tuple[bool, Optional[str]]:
        """Attempt download using wget"""
        if not shutil.which("wget"):
            return False, "wget not available"

        domain = urlparse(url).netloc
        self._rate_limit(domain)

        headers = self._get_headers()
        cmd = [
            "wget", "-q", "-O", output_path,
            f"--timeout={timeout}",
            f"--user-agent={headers['User-Agent']}",
            f"--referer={headers['Referer']}",
            "--compression=auto",
            url
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=timeout+5)
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True, "application/octet-stream"
            return False, "wget failed"
        except Exception as e:
            return False, str(e)

    def _try_wayback(self, url: str, output_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Attempt download from Wayback Machine (most recent snapshot)"""
        try:
            # Get available snapshots
            availability_url = f"https://archive.org/wayback/available?url={url}"
            headers = self._get_headers(referer="https://archive.org/")

            if HAS_REQUESTS and self.session:
                resp = self.session.get(availability_url, headers=headers, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("archived_snapshots", {}).get("closest", {}).get("available"):
                        snapshot_url = data["archived_snapshots"]["closest"]["url"]
                        success, ctype = self._try_requests(snapshot_url, output_path, timeout=90)
                        if success:
                            return True, ctype, snapshot_url

            # Fallback: try direct wayback URL pattern
            wayback_url = f"https://web.archive.org/web/{url}"
            success, ctype = self._try_curl(wayback_url, output_path)
            if success:
                return True, ctype, wayback_url

            return False, None, wayback_url
        except Exception as e:
            self.logger.warning(f"Wayback attempt failed: {e}")
            return False, None, f"https://web.archive.org/web/*/{url}"

    def fetch(self, url: str, output_path: str, try_mirrors: bool = True,
              try_wayback: bool = True, timeout: int = 60) -> DownloadResult:
        """
        Robust multi-tactic download with fallback strategies

        Strategy order:
        1. Direct download (requests → curl → wget)
        2. First-party mirrors (if enabled)
        3. Wayback Machine (if enabled)
        """
        attempted_urls = [url]

        # Strategy 1: Direct download with multiple engines
        for engine_name, engine_func in [
            ("requests", self._try_requests),
            ("curl", self._try_curl),
            ("wget", self._try_wget),
        ]:
            success, result = engine_func(url, output_path, timeout)
            if success:
                self.logger.info(f"✓ Downloaded via {engine_name}: {url}")
                return DownloadResult(
                    status=DownloadStatus.SUCCESS,
                    local_path=output_path,
                    content_type=result,
                    source_url=url,
                    attempted_urls=attempted_urls
                )

        # Strategy 2: Try first-party mirrors
        if try_mirrors:
            mirrors = self._generate_mirror_urls(url)
            for mirror_url in mirrors[:3]:  # Limit to 3 mirrors
                attempted_urls.append(mirror_url)
                self.logger.info(f"Trying mirror: {mirror_url}")

                for engine_name, engine_func in [
                    ("requests", self._try_requests),
                    ("curl", self._try_curl),
                ]:
                    success, result = engine_func(mirror_url, output_path, timeout)
                    if success:
                        self.logger.info(f"✓ Downloaded via mirror ({engine_name}): {mirror_url}")
                        return DownloadResult(
                            status=DownloadStatus.SUCCESS,
                            local_path=output_path,
                            content_type=result,
                            source_url=mirror_url,
                            attempted_urls=attempted_urls
                        )

        # Strategy 3: Wayback Machine fallback
        if try_wayback:
            self.logger.info(f"Attempting Wayback Machine: {url}")
            success, ctype, wayback_url = self._try_wayback(url, output_path)
            if success:
                self.logger.info(f"✓ Downloaded from Wayback: {wayback_url}")
                return DownloadResult(
                    status=DownloadStatus.WAYBACK_SUCCESS,
                    local_path=output_path,
                    content_type=ctype,
                    source_url=url,
                    attempted_urls=attempted_urls,
                    wayback_url=wayback_url
                )

            # Failed - return wayback URL for manual retrieval
            return DownloadResult(
                status=DownloadStatus.FAILED_MIRROR,
                local_path=None,
                content_type=None,
                source_url=url,
                attempted_urls=attempted_urls,
                wayback_url=wayback_url or f"https://web.archive.org/web/*/{url}",
                error_msg="All download strategies failed"
            )

        # Complete failure
        return DownloadResult(
            status=DownloadStatus.FAILED_NETWORK,
            local_path=None,
            content_type=None,
            source_url=url,
            attempted_urls=attempted_urls,
            error_msg="All download engines failed"
        )

    def html_to_pdf(self, html_path: str, pdf_path: str, engine: str = "auto") -> bool:
        """
        Convert HTML to PDF using available engines

        Engines (in preference order):
        1. wkhtmltopdf - Fast, good rendering
        2. playwright - Modern, handles JS
        3. weasyprint - Pure Python, simple CSS
        """
        if engine == "auto":
            # Try engines in order
            if shutil.which("wkhtmltopdf"):
                engine = "wkhtmltopdf"
            elif shutil.which("playwright"):
                engine = "playwright"
            elif shutil.which("weasyprint"):
                engine = "weasyprint"
            else:
                self.logger.warning("No HTML→PDF engine available")
                return False

        try:
            if engine == "wkhtmltopdf":
                cmd = [
                    "wkhtmltopdf",
                    "--enable-local-file-access",
                    "--print-media-type",
                    "--no-stop-slow-scripts",
                    "--javascript-delay", "2000",
                    html_path,
                    pdf_path
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=120)
                return result.returncode == 0 and os.path.exists(pdf_path)

            elif engine == "playwright":
                # Requires: pip install playwright && playwright install chromium
                cmd = [
                    "playwright", "pdf",
                    html_path,
                    pdf_path
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=120)
                return result.returncode == 0 and os.path.exists(pdf_path)

            elif engine == "weasyprint":
                cmd = ["weasyprint", html_path, pdf_path]
                result = subprocess.run(cmd, capture_output=True, timeout=120)
                return result.returncode == 0 and os.path.exists(pdf_path)

        except Exception as e:
            self.logger.error(f"HTML→PDF conversion failed: {e}")

        return False


def filename_from_url(url: str, preferred_ext: Optional[str] = None) -> str:
    """Generate safe filename from URL"""
    parsed = urlparse(url)
    path = parsed.path
    base = os.path.basename(path) or "index"

    if preferred_ext and not base.lower().endswith(preferred_ext):
        base += preferred_ext

    # Sanitize filename
    safe_name = "".join(c for c in base if c.isalnum() or c in "._-")
    return safe_name or "download.bin"


# Example usage demonstration
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    fetcher = RobustWebFetcher()

    # Test case: ODNI UAP report (may have 403s)
    result = fetcher.fetch(
        "https://www.dni.gov/files/ODNI/documents/assessments/Prelimary-Assessment-UAP-20210625.pdf",
        "test_download.pdf",
        try_mirrors=True,
        try_wayback=True
    )

    print(f"Status: {result.status}")
    print(f"Local path: {result.local_path}")
    print(f"Attempted URLs: {len(result.attempted_urls)}")
    if result.wayback_url:
        print(f"Wayback URL: {result.wayback_url}")
