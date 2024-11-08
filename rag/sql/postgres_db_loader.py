import os

from sqlalchemy import create_engine

from rag.parsing.parsing_csv import CSVProcessor
from rag.parsing.parsing_xlsx import XLSXProcessor


def get_postgres_engine():
    db = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT", "5432")
    return create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")


def load_csv_to_db(file_path: str, access_level: int, table_name: str):
    """Loads a CSV file into a PostgreSQL table with an additional access_level column."""
    engine = get_postgres_engine()
    csv_processor = CSVProcessor(file_path)
    df = csv_processor._load_document()

    df["access_level"] = access_level

    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    print(f"Loaded data into table '{table_name}' with access level {access_level}.")
    return engine


def load_xlsx_to_db(file_path: str, sheet_name: str, access_level: int, table_name: str):
    """Loads an Excel sheet into a PostgreSQL table with an additional access_level column."""
    engine = get_postgres_engine()
    xlsx_processor = XLSXProcessor(file_path, sheet_name)
    df = xlsx_processor._load_document()

    df["access_level"] = access_level

    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    print(f"Loaded data into table '{table_name}' with access level {access_level}.")
    return engine


if __name__ == "__main__":  # pragma: no cover
    load_csv_to_db("data/ppl_data_testing - Sheet1.csv", access_level=3, table_name="ppl_data")
