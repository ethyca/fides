import pathlib

import versioneer
from setuptools import find_packages, setup

here = pathlib.Path(__file__).parent.resolve()
long_description = open("README.md").read()

# Requirements

# Explicitly add optional dependencies for conda compatiblity, for instance, avoid using fastapi[all]
install_requires = open("requirements.txt").read().strip().split("\n")
dev_requires = open("dev-requirements.txt").read().strip().split("\n")

# Human-Readable/Reusable Extras
# Add these to `optional-requirements.txt` as well
mysql_connector = "pymysql==1.0.0"
mssql_connector = "pyodbc==4.0.32"
snowflake_connector = "snowflake-sqlalchemy==1.3.4"
redshift_connector = "sqlalchemy-redshift==0.8.8"
aws_connector = "boto3==1.20.54"
okta_connector = "okta==2.5.0"
bigquery_connector = "sqlalchemy-bigquery==1.4.4"

extras = {
    "aws": [aws_connector],
    "mysql": [mysql_connector],
    "mssql": [mssql_connector],
    "okta": [okta_connector],
    "snowflake": [snowflake_connector],
    "redshift": [redshift_connector],
    "bigquery": [bigquery_connector],
}
dangerous_extras = ["mssql"]  # These extras break on certain platforms
extras["all"] = sum(
    [value for key, value in extras.items() if key not in dangerous_extras], []
)

setup(
    name="fidesctl",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="CLI for Fides",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ethyca/fides",
    entry_points={
        "console_scripts": ["fidesctl=fidesctl.cli:cli", "fides=fidesctl.cli:cli"]
    },
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
