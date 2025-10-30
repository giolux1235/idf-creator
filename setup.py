"""Setup script for IDF Creator."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="idf-creator",
    version="1.0.0",
    author="IDF Creator",
    description="Generate EnergyPlus IDF files from minimal inputs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyenergyplus>=0.9.0",
        "requests>=2.31.0",
        "geopy>=2.4.0",
        "pillow>=10.0.0",
        "pytesseract>=0.3.10",
        "PyPDF2>=3.0.1",
        "pdf2image>=1.16.3",
        "opencv-python>=4.8.0.74",
        "pandas>=2.1.0",
        "numpy>=1.24.3",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "idf-creator=main:main",
        ],
    },
)








