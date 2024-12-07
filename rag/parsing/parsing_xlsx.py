from pathlib import Path
import pandas as pd
from llama_index.core.llms import ChatMessage
from llama_index.core.prompts import ChatPromptTemplate
from llama_index.llms.openai import OpenAI
from rag.parsing.processor import FileProcessor, TableInfo


class XLSXProcessor(FileProcessor):
    def __init__(self, document_path, sheet_name=None, llm_model="gpt-4o-mini"):
        """
        Initialize the XLSXProcessor.

        Args:
            document_path (str or Path): Path to the XLSX file.
            sheet_name (str, optional): Specific sheet name to load. Defaults to None.
            llm_model (str): Model name for the LLM. Defaults to "gpt-4o-mini".
        """
        self.document_path = Path(document_path)
        self.sheet_name = sheet_name
        self.llm = OpenAI(model=llm_model)
        self.df = None

    @staticmethod
    def _get_prompt_template():
        """
        Creates a chat prompt template for table summary generation.

        Returns:
            ChatPromptTemplate: Template for generating table summaries.
        """
        prompt_str = """\
        Buat summary terkait table dengan menggunakan JSON format dalam bahasa Indonesia.

        - The table name must be unique to the table and describe it while being concise. 
        - Do NOT output a generic table name (e.g. table, my_table).

        Table:
        {table_str}

        Summary: """
        return ChatPromptTemplate(
            message_templates=[ChatMessage.from_str(prompt_str, role="user")]
        )

    def _load_document(self):
        """
        Loads the XLSX document into a DataFrame.

        Returns:
            pd.DataFrame: Loaded DataFrame.

        Raises:
            RuntimeError: If the file cannot be found or loaded.
        """
        try:
            return pd.read_excel(self.document_path, sheet_name=self.sheet_name)
        except FileNotFoundError:
            raise RuntimeError(f"File not found: {self.document_path}")
        except ValueError as e:
            raise RuntimeError(
                f"Sheet '{self.sheet_name}' not found in the file: {self.document_path}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load document due to an unexpected error: {str(e)}"
            )

    def _generate_table_summary(self):
        """
        Generates a summary for the table using the LLM.

        Returns:
            TableInfo: Table summary information.

        Raises:
            RuntimeError: If the DataFrame is not loaded.
        """
        if self.df is None:
            raise RuntimeError("DataFrame is not loaded. Please load the document first.")

        df_preview = self.df.head(10).to_csv()
        return self.llm.structured_predict(
            TableInfo,
            prompt=self._get_prompt_template(),
            table_str=df_preview,
        )

    def process(self):
        """
        Main processing method: loads the document and generates table info.

        Returns:
            TableInfo: Generated table summary information.
        """
        self.df = self._load_document()
        return self._generate_table_summary()
