#!/usr/bin/env python3
"""
Setup script for VLESS VPN Client - SaaS Production Edition
Commercial-grade VPN solution for enterprise deployment.

© 2024 VPN Solutions Inc. All rights reserved.
"""

from setuptools import setup, find_packages
from pathlib import Path
import sys

# Read README for long description
def read_readme():
    readme_path = Path(__file__).parent / "README-SAAS.md"
    if readme_path.exists():
        return readme_path.read_text(encoding="utf-8", errors="ignore")
    return ""

# Read version
def get_version():
    return "3.0.0"

# Requirements
requirements = []  # No external dependencies for core functionality

# Optional dependencies
extras_require = {
    "gui": ["PyQt5>=5.15.0"],
    "dev": ["pytest>=7.0.0", "black>=22.0.0", "mypy>=0.950"],
}

setup(
    name="vless-vpn-saas",
    version=get_version(),
    author="VPN Solutions Development Team",
    author_email="dev@vpnsolutions.io",
    description="Enterprise-grade VLESS VPN Client for commercial deployment",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://vpnsolutions.io",
    project_urls={
        "Documentation": "https://docs.vpnsolutions.io",
        "Support": "mailto:support@vpnsolutions.io",
        "Sales": "mailto:sales@vpnsolutions.io",
    },
    license="PROPRIETARY",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Security",
        "Topic :: Internet :: Proxy Servers",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    keywords="vpn vless reality enterprise saas commercial",
    py_modules=["vless_client_saas"],
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "vless-vpn=vless_client_saas:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["LICENSE.md", "README-SAAS.md"],
    },
    scripts=[
        "vpn-gui-saas",  # GUI launcher (to be created)
    ],
    zip_safe=False,
)
