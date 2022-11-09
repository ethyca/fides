import pathlib
from typing import List

from setuptools import find_packages, setup

import versioneer

here = pathlib.Path(__file__).parent.resolve()
long_description = open("README.md", encoding="utf-8").read()

##################
## Requirements ##
##################

install_requires = open("requirements.txt", encoding="utf-8").read().strip().split("\n")
dev_requires = open("dev-requirements.txt", encoding="utf-8").read().strip().split("\n")
dangerous_requires = (
    open("dangerous-requirements.txt", encoding="utf-8").read().strip().split("\n")
)


def optional_requirements(
    dependency_names: List[str], requires: List[str] = dangerous_requires
) -> List[str]:
    """
    Matches the provided dependency names to lines in `optional-requirements.txt`,
    and returns the full dependency string for each one.

    Prevents the need to store version numbers in two places.
    """

    requirements: List[str] = []

    for dependency in dependency_names:
        for optional_dependency in requires:
            if optional_dependency.startswith(dependency):
                requirements.append(optional_dependency)
                break

    if len(requirements) == len(dependency_names):
        return requirements

    raise ModuleNotFoundError


# Human-Readable Extras
# Versions are read from corresponding lines in `optional-requirements.txt`
extras = {
    "mssql": optional_requirements(["pyodbc"], dangerous_requires),
}
dangerous_extras = ["mssql"]  # These extras break on certain platforms
extras["all"] = sum(
    [value for key, value in extras.items() if key not in dangerous_extras], []
)


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
    extras_require=extras,
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries",
    ],
)
