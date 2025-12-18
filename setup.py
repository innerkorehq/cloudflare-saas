"""Setup configuration for cloudflare-saas package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="cloudflare-saas",
    version="1.0.1",
    author="innerkore",
    description="Production-ready async library for multi-tenant SaaS platforms with Cloudflare R2 and Workers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/innerkorehq/cloudflare-saas",
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
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
        "cloudflare>=4.0.0",
        "aioboto3>=12.0.0",
        "aiodns>=3.1.0",
        "pydantic>=2.0.0",
        "python-terraform>=0.10.1",
        "httpx>=0.25.0",
        "tenacity>=8.2.0",
        "asyncpg>=0.29.0",
        "pycares>=4.3.0",
        "botocore>=1.31.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
            "ruff>=0.1.0",
            "bumpversion>=0.6.0",
        ],
        "web": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
        ],
    },
    include_package_data=True,
    package_data={
        "cloudflare_saas": ["worker_template.js"],
    },
)