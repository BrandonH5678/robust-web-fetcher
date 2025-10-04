# Documentation

## Quick Links

- **[Quick Reference](QUICK_REFERENCE.md)** - Copy-paste examples and common scenarios
- **[Integration Guide](INTEGRATION.md)** - Detailed technical documentation
- **[API Reference](#)** - Complete API documentation (see main README)

## Getting Started

1. **Installation**: See main [README.md](../README.md#installation)
2. **Quick Start**: See [Quick Reference](QUICK_REFERENCE.md)
3. **Examples**: See [examples/](../examples/)
4. **Advanced Usage**: See [Integration Guide](INTEGRATION.md)

## Key Concepts

### Download Strategy Cascade

Robust Web Fetcher tries multiple methods in sequence:

1. **requests** (Python library, fast)
2. **curl** (system tool, bypasses some blocks)
3. **wget** (alternative system tool)
4. **Mirror rotation** (tries known first-party mirrors)
5. **Wayback Machine** (Internet Archive fallback)

### Mirror Domains

The library knows about common mirror relationships:

- Government: `dni.gov` ↔ `defense.gov` ↔ `aaro.mil`
- NASA: `nasa.gov` ↔ `science.nasa.gov` ↔ `ntrs.nasa.gov`
- Academic: `arxiv.org` ↔ `export.arxiv.org`

### Rate Limiting

Respects per-domain rate limits to avoid overwhelming servers:

```python
# Conservative (3 seconds between requests)
fetcher = RobustWebFetcher(rate_limit_delay=3.0)

# Default (1.5 seconds)
fetcher = RobustWebFetcher()

# Aggressive (use with caution)
fetcher = RobustWebFetcher(rate_limit_delay=0.5)
```

## Troubleshooting

### All Downloads Return 403

- Increase rate limit delay: `RobustWebFetcher(rate_limit_delay=5.0)`
- Check if site requires authentication (not supported)
- Try manual Wayback URL from `result.wayback_url`

### HTML→PDF Conversion Fails

Install a conversion engine:

```bash
# Option 1: wkhtmltopdf (recommended)
sudo apt install wkhtmltopdf

# Option 2: Playwright
pip install playwright
playwright install chromium

# Option 3: WeasyPrint
pip install weasyprint
```

### Import Errors

Ensure `requests` is installed:

```bash
pip install requests
```

## Contributing

See main [README.md](../README.md#contributing) for contribution guidelines.

## Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/robust-web-fetcher/issues)
- **Examples**: [examples/](../examples/)
- **API Reference**: See main [README.md](../README.md#api-reference)
