from sqlalchemy.engine.base import Engine


def create_citext_extension(engine: Engine) -> None:
    with engine.connect() as con:
        con.execute("CREATE EXTENSION IF NOT EXISTS citext;")
