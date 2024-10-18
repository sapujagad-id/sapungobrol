import unittest
from unittest.mock import patch, MagicMock
from rag.vectordb.pinecone_handler import PineconeHandler
from rag.parsing.parsing_pdf import PDFProcessor

class TestRunPineconeStorage(unittest.TestCase):

    @patch("openai.embeddings.create")
    @patch("os.getenv")
    @patch.object(PineconeHandler, "__init__", return_value=None)
    @patch.object(PineconeHandler, "upsert_vectors")
    @patch.object(PDFProcessor, "process")
    def test_run_pinecone_storage(self, mock_process, mock_upsert_vectors, mock_pinecone_init, mock_getenv, mock_create_embedding):
        mock_getenv.side_effect = lambda key: "test_key" if key in ["PINECONE_API_KEY", "OPENAI_API_KEY"] else None

        mock_process.return_value = [MagicMock(text="Fake Node 1"), MagicMock(text="Fake Node 2")]

        mock_create_embedding.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

        with patch("builtins.print") as mock_print:
            import scripts.run_pinecone_storage

            self.assertEqual(mock_create_embedding.call_count, 0)
