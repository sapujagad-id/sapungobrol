from rag.parsing.parsing_csv import CSVProcessor

from sqlalchemy import create_engine


def load_csv_to_db(file_path: str, db_path: str = "sqlite:///ppl_data.db"):
    csv_processor = CSVProcessor(file_path)
    df = csv_processor._load_document()
    
    engine = create_engine(db_path)

    df.to_sql('ppl_data', con=engine, if_exists='replace', index=False)
    
    return engine
