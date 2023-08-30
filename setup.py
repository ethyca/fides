import pathlib

from setuptools import find_packages, setup

import versioneer

here = pathlib.Path(__file__).parent.resolve()
long_description = open("README.md", encoding="utf-8").read()

##################
## Requirements ##
##################

install_requires = open("requirements.txt", encoding="utf-8").read().strip().split("\n")
dev_requires = open("dev-requirements.txt", encoding="utf-8").read().strip().split("\n")

###################
## Package Setup ##
###################
setup(
    name="ethyca-fides",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Open-source ecosystem for data privacy as code.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ethyca/fides",
    entry_points={"console_scripts": ["fides=fides.cli:cli"]},
    python_requires=">=3.8, <4",
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
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries",
    ],
)
