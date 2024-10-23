from .processor import FileProcessor
from llama_index.readers.file import CSVReader
from pathlib import Path
from llama_index.readers.file.tabular.base import PandasCSVReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.prompts import ChatPromptTemplate
from llama_index.core.bridge.pydantic import BaseModel, Field
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
import os
import pandas as pd


prompt_str = """\
Buat summary terkait table dengan menggunakan JSON format dalam bahasa indonesia.

- The table name must be unique to the table and describe it while being concise. 
- Do NOT output a generic table name (e.g. table, my_table).

Table:
{table_str}

Summary: """

prompt_tmpl = ChatPromptTemplate(
    message_templates=[ChatMessage.from_str(prompt_str, role="user")]
)

class TableInfo(BaseModel):
    
    table_name: str = Field(
        ..., description="table name (must be underscores and NO spaces)"
    )
    table_summary: str = Field(
        ..., description="short, concise summary/caption of the table"
    )

class CSVProcessor(FileProcessor):
    
    def __init__(self, document_path):
        self.document_path = Path(document_path)
        self.llm = OpenAI(model="gpt-3.5-turbo")

    def _get_generate_response(self):

        return ChatPromptTemplate(
            message_templates=[ChatMessage.from_str(prompt_str, role="user")]
        )
    
    def _load_document(self):
        try:
            return pd.read_csv(self.document_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load document: {str(e)}")

    def _get_table_info(self):
        df_str = self.df.head(10).to_csv()
        table_info = self.llm.structured_predict(TableInfo, prompt = self._get_generate_response,
                                            table_str=df_str)
        table_name = table_info.table_name

    def process(self):
        self.df = self._load_document()
        self._get_table_info()
    
if __name__=="__main__":
    csv_processor = CSVProcessor('data/ppl_data_testing - Sheet1.csv')
    file = csv_processor.load_document()
    print(file)
