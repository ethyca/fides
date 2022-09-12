import pathlib

from setuptools import find_packages, setup

import versioneer

here = pathlib.Path(__file__).parent.resolve()
long_description = open("README.md").read()

##################
## Requirements ##
##################

install_requires = open("requirements.txt").read().strip().split("\n")
dev_requires = open("dev-requirements.txt").read().strip().split("\n")

# Human-Readable Extras
# Add these to `optional-requirements.txt` as well for Docker caching
aws = ["boto3~=1.24.46"]
bigquery = ["sqlalchemy-bigquery==1.4.4"]
mongo = ["pymongo==3.12.0"]
mssql = ["pyodbc==4.0.34"]
mysql = ["pymysql==1.0.2"]
okta = ["okta==2.5.0"]
redis = ["redis==3.5.3", "fastapi-caching[redis]"]
redshift = ["sqlalchemy-redshift==0.8.11"]
snowflake = ["snowflake-sqlalchemy==1.3.4"]

extras = {
    "aws": aws,
    "bigquery": bigquery,
    "mongo": mongo,
    "mssql": mssql,
    "mysql": mysql,
    "okta": okta,
    "redis": redis,
    "redshift": redshift,
    "snowflake": snowflake,
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
    python_requires=">=3.9, <4",
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries",
    ],
)
