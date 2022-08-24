import pathlib

from setuptools import find_packages, setup

import versioneer

here = pathlib.Path(__file__).parent.resolve()
long_description = open("README.md").read()

# Requirements

# Explicitly add optional dependencies for conda compatiblity,
# for instance, avoid using fastapi[all]
install_requires = open("requirements.txt").read().strip().split("\n")
dev_requires = open("dev-requirements.txt").read().strip().split("\n")

# Human-Readable/Reusable Extras
# Add these to `optional-requirements.txt` as well

setup(
    name="ethyca-fides",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Open-source ecosystem for data privacy as code.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ethyca/fides",
    entry_points={"console_scripts": ["fides=fides.cli:cli"]},
    python_requires=">=3.9, <4",
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries",
    ],
)
