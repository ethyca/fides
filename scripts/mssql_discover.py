# This file is not committed to the repo, please create secrets.py with the required
# variables in the same dir as this file before running this script
from secrets import DB, IP, PASS, PORT, USER

import sqlalchemy

MASTER_MSSQL_URL = f"mssql+pyodbc://{USER}:{PASS}@{IP}:{PORT}/{DB}?driver=ODBC+Driver+17+for+SQL+Server"


SUPPORTED_DATA_TYPES = set(
    [
        # char types
        "varchar",
        "nvarchar",
        "char",
        "nchar",
        "ntext",
        "text",
        # numeric types
        "int",
        "bigint",
        "smallint",
        "tinyint",
        "money",
        "float",
        "decimal",
        # date types
        "date",
        "datetime",
        "datetime2",
        "smalldatetime",
        # other types
        "bit",
    ]
)


def mssql_discover():
    """
    Select all databases from the instance
    Select the schema data for each data base
    Check if there are any fields in the schema that Fidesops does not yet support
    """
    engine = sqlalchemy.create_engine(MASTER_MSSQL_URL)
    all_dbs = engine.execute("SELECT name FROM sys.databases;").all()
    all_columns = []
    flagged_columns = []
    flagged_datatypes = set()
    for db_name in all_dbs:
        db_name = db_name[0]
        try:
            columns = engine.execute(
                f"SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM {db_name}.INFORMATION_SCHEMA.COLUMNS;"
            ).all()
        except Exception:
            continue

        all_columns.extend(columns)
        for table, column, data_type in columns:
            if data_type not in SUPPORTED_DATA_TYPES:
                flagged_datatypes.add(data_type)
                flagged_columns.append(f"{db_name}.{table}.{column}: {data_type}")

    print(f"{len(all_columns)} columns found")
    print(f"{len(flagged_columns)} columns flagged")
    print(f"Flagged datatypes:")
    print(",\n".join(flagged_datatypes))
    print(f"Flagged columns:")
    print(",\n".join(flagged_columns))


if __name__ == "__main__":
    mssql_discover()
