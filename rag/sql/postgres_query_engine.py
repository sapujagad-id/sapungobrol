# python -m rag.sql.postgres_query_engine
from llama_index.core import SQLDatabase
from llama_index.core.llms import ChatMessage
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.llms.openai import OpenAI
from sqlalchemy import text

from rag.sql.local.local_query_engine import (extract_signature,
                                              get_table_schema)
from rag.sql.postgres_db_loader import get_postgres_engine
from rag.sql.security import check_sql_security


def setup_llm():
    return OpenAI(model="gpt-4o-mini")

def setup_query_engine(table_name: str):
    llm = setup_llm()
    engine = get_postgres_engine()
    sql_database = SQLDatabase(engine)
    table_schema = get_table_schema(engine, table_name)

    query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database, tables=[table_name], llm=llm
    )

    return query_engine, table_schema


def run_query(query_str: str, user_access_level: int, table_name: str):
    llm = setup_llm()
    query_engine, table_schema = setup_query_engine(table_name=table_name)

    _, signature = extract_signature(query_str)
    
    prompt_with_schema = f"""
    You are querying a table with the following columns: 
    {', '.join(table_schema)}.
    
    When generating SQL queries, note that the table is in a PostgreSQL database. Column names containing spaces must be enclosed in double quotes. Also, be wary of SQL injection attacks. Make sure that the query is not malicious.
    Include a condition to filter rows based on the user's access level: only retrieve rows where `access_level` <= {user_access_level}.

    Question: {query_str}
    """
    
    response = query_engine.query(prompt_with_schema)
    generated_sql = response.metadata.get('sql_query', '')

    is_valid, message = check_sql_security(generated_sql, signature)
    if not is_valid:
        raise ValueError(f"Security check failed: {message}")
      
    filtered_query = generated_sql.rstrip(";")
    filtered_query += f" AND access_level <= {user_access_level}"

    engine = get_postgres_engine()
    with engine.connect() as connection:
        result = connection.execute(text(filtered_query))
        rows = result.fetchall()

    if rows:
      formatted_data = "\n".join([", ".join(map(str, row)) for row in rows])
      follow_up_prompt = f"""
      Based on the question "{query_str}", here is the data retrieved:

      {formatted_data}

      Please respond concisely and professionally, providing only the essential information in a clear and direct manner.
      """
      messages = [
          ChatMessage(role="user", content=follow_up_prompt)
      ]
      final_response = llm.chat(messages).message.content
    else:
        final_response = "I'm sorry, but there is no data available for your access level or the specified query."

    return final_response


if __name__ == "__main__":  # pragma: no cover
    table_name = "ppl_data"
    user_access_level = 2

    query = "What is the total value approved for the week of September 23, 2024?"
    response = run_query(query, user_access_level=user_access_level, table_name=table_name)

    print(response)
