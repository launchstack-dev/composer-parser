#!/usr/bin/env python3
"""
Setup script for Composer Parser
A Python library for parsing and backtesting Composer.trade strategies
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements from requirements.txt
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Get version from a version file or use default
def get_version():
    version_file = os.path.join("composer_parser", "version.py")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            exec(f.read())
            return locals()["__version__"]
    return "1.0.0"

setup(
    name="composer-parser",
    version=get_version(),
    author="Jensen Carlsen",
    author_email="jensen@example.com",  # Update with your email
    description="A Python library for parsing and backtesting Composer.trade strategies",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/jensencarlsen/composer-parser",
    project_urls={
        "Bug Tracker": "https://github.com/jensencarlsen/composer-parser/issues",
        "Documentation": "https://github.com/jensencarlsen/composer-parser#readme",
        "Source Code": "https://github.com/jensencarlsen/composer-parser",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # "composer-backtest=backtester:run_backtest",  # Removed deprecated entry point
        ],
    },
    include_package_data=True,
    package_data={
        "composer_parser": [
            "*.json",
            "*.csv",
        ],
    },
    keywords=[
        "composer",
        "trading",
        "strategy",
        "backtesting",
        "financial",
        "investment",
        "algorithmic-trading",
        "technical-analysis",
        "portfolio-management",
    ],
    platforms=["any"],
    license="MIT",
    zip_safe=False,
) 