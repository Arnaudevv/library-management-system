from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def migrate_loan_due_date(engine: Engine) -> None:
    """Add the planned return date to existing loan tables."""
    inspector = inspect(engine)
    if "loan" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("loan")}
    if "due_date" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE loan ADD COLUMN due_date DATE"))
