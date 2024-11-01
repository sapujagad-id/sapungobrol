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
            db_conn_url="mysql://user:password@localhost:3210/dbname",
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

    def test_missing_table_names_for_sql_type(self):
        data_source = DataSource(
            id=uuid4(),
            type=DataSourceType.SQL,
            object_url=None,
            db_conn_url="postgresql://user:password@localhost/dbname",
            table_names=None,
            created_by=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        with pytest.raises(TableNameError):
            data_source.validate()

    def test_missing_table_names_for_csv_type(self):
        data_source = DataSource(
            id=uuid4(),
            type=DataSourceType.CSV,
            object_url=None,
            db_conn_url="sqlite:///example.db",
            table_names=None,
            created_by=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        with pytest.raises(TableNameError):
            data_source.validate()

    def test_missing_object_url_for_pdf_type(self):
        data_source = DataSource(
            id=uuid4(),
            type=DataSourceType.PDF,
            object_url="asd",
            db_conn_url=None,
            table_names=None,
            created_by=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        data_source.object_url = None
        with pytest.raises(ObjectUrlError):
            data_source.validate()

    def test_invalid_data_source_type(self):
        data_source = DataSource(
            id=uuid4(),
            type=DataSourceType.PDF,
            object_url=None,
            db_conn_url=None,
            table_names=None,
            created_by=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        data_source.type = "invalido"
        with pytest.raises(DataSourceTypeError):
            data_source.validate()