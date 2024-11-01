from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import UUID4, BaseModel

class TableNameError(Exception):
    def __init__(self, message="Tabular data requires SQL table names"):
        self.message = message
        super().__init__(self.message)
        
class ObjectUrlError(Exception):
    def __init__(self, message="Object data requires URL to the object"):
        self.message = message
        super().__init__(self.message)
        
class DataSourceTypeError(Exception):
    def __init__(self, message="Data Source Type is not valid"):
        self.message = message
        super().__init__(self.message)  

class DataSourceType(str, Enum):
    CSV = "csv"
    PDF = "pdf"
    TXT = "txt"
    SQL = "sql"

class DataSource(BaseModel):
    id: UUID4
    type: DataSourceType
    
    # for object storage
    object_url: Optional[str]
    
    # for tabular data
    db_conn_url: Optional[str]
    table_names: Optional[list[str]]
    
    created_by: UUID4
    created_at: datetime
    updated_at: datetime
    
    def validate(self):
      if self.type not in DataSourceType._value2member_map_:
        print(DataSourceType._value2member_map_)
        raise DataSourceTypeError
      elif self.type == DataSourceType.CSV or self.type == DataSourceType.SQL:
        if self.table_names is None or len(self.table_names) == 0:
          raise TableNameError
      elif self.type == DataSourceType.PDF or self.type == DataSourceType.TXT:
        if not self.object_url:
          raise ObjectUrlError