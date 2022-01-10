import sqlalchemy

MSSQL_URL_TEMPLATE = "mssql+pyodbc://sa:Mssql_pw1@mssql_example:1433/{}?driver=ODBC+Driver+17+for+SQL+Server"
MASTER_MSSQL_URL = MSSQL_URL_TEMPLATE.format("master") + "&autocommit=True"


def mssql_setup():
    """
    Set up the SQL Server Database for testing.
    The query file must have each query on a separate line.
    Initial connection must be done to the master database.
    """
    engine = sqlalchemy.create_engine(MASTER_MSSQL_URL)
    with open("data/sql/mssql_example.sql", "r") as query_file:
        queries = [query for query in query_file.read().splitlines() if query != ""]
    for query in queries:
        engine.execute(sqlalchemy.sql.text(query))


if __name__ == "__main__":
    mssql_setup()
