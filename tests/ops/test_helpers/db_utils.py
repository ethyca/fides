from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database


def seed_postgres_data(db: Session, query_file_path: str) -> Session:
    """
    :param db: SQLAlchemy session for the Postgres DB
    :param query_file_path: file path pointing to the `.sql` file
     that contains the query to seed the data in the DB. e.g.,
     `./docker/sample_data/postgres_example.sql`

    Using the provided sesion, creates the database, dropping it if it
    already existed. Seeds the created database using the query found
    in the  relative path provided. Some processing is done on the query
    text so that it can be executed properly.
    """
    if database_exists(db.bind.url):
        # Postgres cannot drop databases from within a transaction block, so
        # we should drop the DB this way instead
        drop_database(db.bind.url)
    create_database(db.bind.url)
    with open(query_file_path, "r") as query_file:
        lines = query_file.read().splitlines()
        filtered = [line for line in lines if not line.startswith("--")]
        queries = " ".join(filtered).split(";")
        [db.execute(f"{text(query.strip())};") for query in queries if query]
    return db
