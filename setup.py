#!/usr/bin/env python3
"""
Robust Web Fetcher - Setup script
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="robust-web-fetcher",
    version="1.0.0",
    author="Robust Web Fetcher Contributors",
    author_email="your.email@example.com",
    description="Multi-tactic download library for stubborn sites, 403 errors, and unreliable sources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YOUR_USERNAME/robust-web-fetcher",
    packages=find_packages(),
    py_modules=["robust_web_fetcher"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
    ],
    extras_require={
        "pdf": [
            "playwright>=1.40.0",
            "weasyprint>=60.0",
        ],
        "dev": [
            "pytest>=7.0",
            "black>=23.0",
            "pylint>=2.17",
        ],
    },
    entry_points={
        "console_scripts": [
            "robust-fetch=robust_web_fetcher:main",
        ],
    },
)
