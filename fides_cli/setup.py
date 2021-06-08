import os
import pathlib
from setuptools import setup, find_packages

here = pathlib.Path(__file__).parent.resolve()
long_description = "CLI for Fides"

# Requirements
install_requires = open("requirements.txt").read().strip().split("\n")
dev_requires = open("dev-requirements.txt").read().strip().split("\n")
version = "0.0.9"

setup(
    name="fidesctl",
    version=version,
    description="CLI for Fides",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/ethyca/fides-core",
    entry_points={"console_scripts": ["fidesctl=fides.cli:cli"]},
    python_requires=">=3.7, <4",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    author="Ethyca, Inc.",
    author_email="fidesteam@ethyca.com",
    license="Apache License 2.0",
    install_requires=install_requires,
    dev_requires=dev_requires,
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries",
    ],
)
