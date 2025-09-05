#!/usr/bin/env python3
"""Setup script for YouTube Music Manager."""

from setuptools import setup, find_packages

# Read requirements
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read README for long description
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="youtube-music-manager",
    version="0.1.0",
    author="Christian",
    description="Clean CLI tool for managing YouTube Music artist subscriptions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        'console_scripts': [
            'ytmusic-manager=ytmusic_manager.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: System :: Systems Administration",
    ],
    keywords="youtube music subscription management cli automation",
    project_urls={
        "Bug Reports": "https://github.com/user/youtube-music-manager/issues",
        "Source": "https://github.com/user/youtube-music-manager",
    },
)