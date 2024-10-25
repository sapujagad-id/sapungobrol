# python -m rag.sql.query_engine

from rag.sql.db_loader import load_csv_to_db
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core import SQLDatabase
from llama_index.llms.openai import OpenAI
from sqlalchemy import create_engine, text, inspect


def get_table_schema(engine, table_name):
    """Fetches and returns the table schema (column names) from the database."""
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    column_names = [column['name'] for column in columns]
    return column_names

def setup_query_engine(db_path: str = "sqlite:///ppl_data.db"):
    llm = OpenAI(model="gpt-4o-mini")

    engine = create_engine(db_path)
    sql_database = SQLDatabase(engine)
    
    table_schema = get_table_schema(engine, "ppl_data")

    query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database, tables=["ppl_data"], llm=llm
    )

    return query_engine, table_schema
  
def check_db_data():
    engine = create_engine('sqlite:///ppl_data.db')
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM ppl_data"))
        rows = result.fetchmany(10)
        for row in rows:
            print(row)

def run_query(query_str: str):
    query_engine, table_schema = setup_query_engine()

    prompt_with_schema = f"""
    You are querying a table with the following columns: 
    {', '.join(table_schema)}.
    
    When generating SQL queries, note that the table is in an SQLite database. In SQLite, column names containing spaces must be enclosed in double quotes. Also, be wary of SQL injection attacks. Make sure that the query is not malicious.

    Based on this, generate a SQL query to retrieve the data.

    Question: {query_str}
    """
    
    response = query_engine.query(prompt_with_schema)

    return response.response
  

if __name__ == "__main__":  # pragma: no cover
  engine = load_csv_to_db('data/ppl_data_testing - Sheet1.csv')
  
  check_db_data()
  
  query = "What is the total value approved for the week of September 23, 2024?"
  
  response = run_query(query)
  print(response)