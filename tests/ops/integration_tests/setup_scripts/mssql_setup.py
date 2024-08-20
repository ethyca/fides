from time import sleep

import pymssql
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError

from fides.api.models.privacy_experience import PrivacyExperienceConfig

MSSQL_URL_TEMPLATE = "mssql+pymssql://sa:Mssql_pw1@mssql_example:1433/{}"
MASTER_MSSQL_URL = MSSQL_URL_TEMPLATE.format("master")

SERVER = "mssql_example"
USER = "sa"
PASSWORD = "Mssql_pw1"
DATABASE = "master"


def mssql_setup():
    """
    Set up the SQL Server Database for testing.
    The query file must have each query on a separate line.
    Initial connection must be done to the master database.
    """
    engine = sqlalchemy.create_engine(MASTER_MSSQL_URL)

    # Wait until mssql is ready. MSSQL tests were randomly failing in CI because the
    # server wasn't ready. This is a workaround to that issue.
    try_number = 1
    while True:
        try:
            # Just need to verify connection is possible so try then close it right away
            conn = engine.connect()
            conn.close()
            break
        except SQLAlchemyError:
            try_number += 1
            print(
                f"Error connecting with URL: {MASTER_MSSQL_URL}\nRetrying...Try number {try_number}"
            )
            sleep(1)

    with open("./docker/sample_data/mssql_example.sql", "r") as query_file:
        queries = [query for query in query_file.read().splitlines() if query != ""]

    # This must be done within a direct connection to enable autocommit
    with pymssql.connect(
        SERVER, USER, PASSWORD, DATABASE, autocommit=True
    ) as connection:
        for query in queries:
            with connection.cursor() as cursor:
                cursor.execute(query)


if __name__ == "__main__":
    try:
        mssql_setup()
    except ModuleNotFoundError:
        print("MSSQL Drivers not installed, skipping setup...")
