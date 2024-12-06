from pathlib import Path

import pandas as pd
from llama_index.core.llms import ChatMessage
from llama_index.core.prompts import ChatPromptTemplate
from llama_index.llms.openai import OpenAI

from rag.parsing.processor import FileProcessor, TableInfo


class CSVProcessor(FileProcessor):
    
    def __init__(self, document_path):
        self.document_path = Path(document_path)
        self.llm = OpenAI(model="gpt-4o-mini")
        self.df = None  # Initialize dataframe attribute

    def _get_prompt_template(self):
        """Returns the prompt template for table summary generation."""
        prompt_str = """\
        Buat summary terkait table dengan menggunakan JSON format dalam bahasa indonesia.

        - The table name must be unique to the table and describe it while being concise. 
        - Do NOT output a generic table name (e.g. table, my_table).

        Table:
        {table_str}

        Summary: """
        
        return ChatPromptTemplate(
            message_templates=[ChatMessage.from_str(prompt_str, role="user")]
        )

    def _load_document(self):
        """Loads the CSV document into a pandas DataFrame."""
        try:
            self.df = pd.read_csv(self.document_path)
            return self.df
        except Exception as e:
            raise RuntimeError(f"Failed to load document: {str(e)}")

    def _get_table_info(self):
        """Generates table information using the loaded DataFrame and LLM."""
        if self.df is None:
            raise RuntimeError("DataFrame is not loaded.")
        
        df_str = self.df.head(10).to_csv()
        table_info = self.llm.structured_predict(
            TableInfo, 
            prompt=self._get_prompt_template(),
            table_str=df_str
        )
        
        return table_info

    def process(self):
        """Main processing method: loads the document and generates table info."""
        self.df = self._load_document()
        table_info = self._get_table_info()
        return table_info
    
if __name__=="__main__":  # pragma: no cover
    csv_processor = CSVProcessor('data/ppl_data_testing - Sheet1.csv')
    file = csv_processor._load_document()
    print(file)