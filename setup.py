"""A setuptools based setup module.

See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="seeker-cornell",  # Required
    version="1.0.1",  # Required
    description="Search Engine for Efficient Knowledge Extraction and Retrieval",  # Optional
    long_description=long_description,  # Optional
    long_description_content_type="text/markdown",  # Optional (see note above)
    url="https://github.com/CornellDB/SEEKER/",  # Optional
    author="Santiago Martínez Novoa",  # Optional
    author_email="sm2936@cornell.edu",  # Optional
    classifiers=[  # Optional
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="search, knowledge extraction, retrieval",  # Updated keywords
    package_dir={"": "seeker/src"},  # Optional
    packages=find_packages(where="seeker/src"),  # Required
    python_requires=">=3.7, <4",
    install_requires=[
        "bson>=0.5.10",
        "pandas>=1.0.0",  # Added pandas
        # `re`, `uuid`, `os`, `json` are part of the standard library and do not need to be included
    ],
    extras_require={  # Optional
        "dev": ["pytest>=7.0", "twine>=4.0.2"],
    },
)
