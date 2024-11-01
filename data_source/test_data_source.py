import pytest
from datetime import datetime
from uuid import uuid4
from data_source import DataSource, DataSourceType, TableNameError, ObjectUrlError, DataSourceTypeError

class TestDataSource:
    def test_valid_sql_data_source(self):
        data_source = DataSource(
            id=uuid4(),
            type=DataSourceType.SQL,
            object_url=None,
            db_conn_url="postgresql://user:password@localhost/dbname",
            table_names=["users", "orders"],
            created_by=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        data_source.validate()

    def test_valid_csv_data_source(self):
        data_source = DataSource(
            id=uuid4(),
            type=DataSourceType.CSV,
            object_url=None,
            db_conn_url="sqlite:///example.db",
            table_names=["users"],
            created_by=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        data_source.validate()

    def test_valid_pdf_data_source(self):
        data_source = DataSource(
            id=uuid4(),
            type=DataSourceType.PDF,
            object_url="https://example.com/report.pdf",
            db_conn_url=None,
            table_names=None,
            created_by=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        data_source.validate()
