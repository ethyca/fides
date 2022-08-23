from time import sleep

import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError

MSSQL_URL_TEMPLATE = "mssql+pyodbc://sa:Mssql_pw1@mssql_example:1433/{}?driver=ODBC+Driver+17+for+SQL+Server"
MASTER_MSSQL_URL = MSSQL_URL_TEMPLATE.format("master") + "&autocommit=True"


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
            print(f"Error connecting, retrying. Try number {try_number}")
            sleep(1)

    with open("./docker/sample_data/mssql_example.sql", "r") as query_file:
        queries = [query for query in query_file.read().splitlines() if query != ""]
    for query in queries:
        engine.execute(sqlalchemy.sql.text(query))


if __name__ == "__main__":
    mssql_setup()
