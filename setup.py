import pathlib
import subprocess
from distutils.cmd import Command

import versioneer
from setuptools import find_packages, setup
from setuptools.command.build_py import build_py


class NPMExportCommand(Command):
    """Custom command to export our frontend UI"""

    description = "build the UI via npm"
    user_options = [("client-name=", None, "name of client to export")]

    def initialize_options(self) -> None:
        """Set default values for options. We only have the admin-ui
        right now, so set that as the default."""
        self.client_name = "admin-ui"

    def finalize_options(self) -> None:
        """Post-process options"""
        return

    def run(self) -> None:
        """Run npm export"""
        directory = f"clients/{self.client_name}"
        install_command = "npm install"
        build_command = "npm run prod-export"
        subprocess.check_call(install_command.split(" "), cwd=directory)
        subprocess.check_call(build_command.split(" "), cwd=directory)


class BuildPyCommand(build_py):
    """Extend the default build_py command to also call our custom npm export command"""

    def run(self) -> None:
        self.run_command("npm_export")
        build_py.run(self)


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

versioneer_cmdclass = versioneer.get_cmdclass()
npm_export_cmdclass = {"npm_export": NPMExportCommand}
build_py_cmdclass = {"build_py": BuildPyCommand}

setup(
    name="fidesctl",
    version=versioneer.get_version(),
    cmdclass={**versioneer_cmdclass, **npm_export_cmdclass, **build_py_cmdclass},
    description="CLI for Fides",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ethyca/fides",
    entry_points={
        "console_scripts": ["fidesctl=fidesctl.cli:cli", "fides=fidesctl.cli:cli"]
    },
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
        "Topic :: Software Development :: Libraries",
    ],
)
