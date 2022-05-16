import pathlib

from setuptools import find_packages, setup

import versioneer

here = pathlib.Path(__file__).parent.resolve()
long_description = open("README.md").read()

# Requirements
install_requires = open("requirements.txt").read().strip().split("\n")
dev_requires = open("dev-requirements.txt").read().strip().split("\n")

setup(
    name="fidesops",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Automation engine for privacy requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ethyca/fidesops",
    entry_points={"console_scripts": ["fidesops=fidesops.cli:cli"]},
    python_requires=">=3.7, <4",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data={"fidesops": ["alembic.ini"]},
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
