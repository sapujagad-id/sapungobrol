from sqlalchemy import create_engine

from rag.parsing.parsing_csv import CSVProcessor
from rag.parsing.parsing_xlsx import XLSXProcessor


def load_csv_to_db(file_path: str, db_path: str = "sqlite:///ppl_data.db"):
    csv_processor = CSVProcessor(file_path)
    df = csv_processor._load_document()
    
    engine = create_engine(db_path)

    df.to_sql('ppl_data', con=engine, if_exists='replace', index=False)
    
    return engine

def load_xlsx_to_db(file_path: str, sheet_name: str, db_path: str = "sqlite:///ppl_data.db"):
    xlsx_processor = XLSXProcessor(file_path, sheet_name)
    df = xlsx_processor._load_document()
    
    engine = create_engine(db_path)

    df.to_sql('ppl_data', con=engine, if_exists='replace', index=False)
    
    return engine