from abc import ABC, abstractmethod
from typing import Annotated

from fastapi import Body, File, Form, HTTPException, UploadFile
from loguru import logger
from document import DocumentFilter, DocumentCreate, DocumentUpdate
from document.document import Document, DocumentTitleError, DocumentTypeError, ObjectNameError
from document.service import DocumentService


class DocumentController(ABC):
    @abstractmethod
    def fetch_documents(self, filter: DocumentFilter):
        pass
      
    @abstractmethod
    def fetch_document_by_name(self, object_name: str):
        pass
      
    @abstractmethod
    def fetch_document_by_id(self, doc_id: str):
        pass

    @abstractmethod
    def upload_document(self, request: DocumentCreate):
        pass

    @abstractmethod
    def update_document(self, doc_id: str, request: DocumentUpdate):
        pass
    
    @abstractmethod
    def delete_document(self, doc_id: str):
        pass
      
class DocumentControllerV1(ABC):
    def __init__(self, service: DocumentService):
        self.service = service
        self.logger = logger.bind(service="DocumentController")
        super().__init__()
        
    def fetch_documents(
      self, 
      id: str | None = None,
      object_name: str | None = None,
      created_after: str | None = None,
      created_before: str | None = None,
      updated_after: str | None = None,
      updated_before: str | None = None,
    ):
        doc_filter = DocumentFilter(
          id = id,
          object_name = object_name,
          created_after = created_after,
          created_before = created_before,
          updated_after = updated_after,
          updated_before = updated_before,
        )
        try:
            docs = self.service.get_documents(filter=doc_filter)
            if docs is None:
                raise HTTPException(status_code=404)
            return docs
        except Exception as e:
            self.logger.error(e.args)
            raise HTTPException(status_code=500)
      
    def fetch_document_by_name(self, object_name: str):
        try:
            doc = self.service.get_document_by_name(object_name=object_name)
            if doc is None:
                raise HTTPException(status_code=404)
            return doc
        except Exception as e:
            self.logger.error(e.args)
            raise HTTPException(status_code=500)
      
    def fetch_document_by_id(self, doc_id: str):
        try:
            doc = self.service.get_document_by_id(doc_id=doc_id)
            if doc is None:
                raise HTTPException(status_code=404)
            return doc
        except Exception as e:
            self.logger.error(e.args)
            raise HTTPException(status_code=500)

    def upload_document(self, 
      file: Annotated[UploadFile, File()], 
      type: Annotated[str, Form()],
      object_name: Annotated[str, Form()],
      title: Annotated[str, Form()],
    ):
        doc_create = DocumentCreate(
          type=type,
          object_name=object_name,
          title=title,
        )
        
        # TODO: S3 integration (upload file)
        self.logger.info(file.filename)
        
        try:
            self.service.create_document(request=doc_create)
            return {"detail": "Document created successfully!"}
        except DocumentTypeError as exc:
            raise HTTPException(status_code=400, detail=exc.message)
        except DocumentTitleError as exc:
            raise HTTPException(status_code=400, detail=exc.message)
        except ObjectNameError as exc:
            raise HTTPException(status_code=400, detail=exc.message)
        except Exception as e:
            self.logger.error(e.args)
            raise HTTPException(status_code=500)

    def update_document(self, doc_id: str, request: DocumentUpdate):
        raise HTTPException(status_code=501) # 501 Not Implemented
    
    def delete_document(self, doc_id: str):
        raise HTTPException(status_code=501) # 501 Not Implemented