from abc import ABC, abstractmethod

from document.document import ObjectNameError
from document.dto import DocumentCreate, DocumentFilter, DocumentResponse, DocumentUpdate
from document.repository import DocumentRepository


class DocumentService(ABC):
    @abstractmethod
    def get_documents(self, filter: DocumentFilter) -> list[DocumentResponse]:
        pass
      
    @abstractmethod
    def get_document_by_name(self, object_name: str) -> DocumentResponse:
        pass
      
    @abstractmethod
    def get_document_by_id(self, doc_id: str) -> DocumentResponse:
        pass

    @abstractmethod
    def create_document(self, request: DocumentCreate):
        pass

    # note: Not implemented to ensure vector database and document entries are not out of sync
    # @abstractmethod
    # def update_document(self, doc_id: str, request: DocumentUpdate):
    #     pass
    
    # @abstractmethod
    # def delete_document(self, doc_id: str):
    #     pass
      
class DocumentServiceV1(DocumentService):
    def __init__(self, repository: DocumentRepository):
        super().__init__()
        self.repository = repository
        
    def get_documents(self, filter: DocumentFilter) -> list[DocumentResponse] | None:
        docs = self.repository.get_documents(filter=filter)
        return docs if docs else None
      
    def get_document_by_name(self, object_name: str) -> DocumentResponse | None:
        doc = self.repository.get_document_by_name(object_name=object_name)
        return doc if doc else None
      
    def get_document_by_id(self, doc_id: str) -> DocumentResponse | None:
        doc = self.repository.get_document_by_id(doc_id=doc_id)
        return doc if doc else None

    def create_document(self, request: DocumentCreate):
        request.validate()
        print(request.model_dump())
        if self.repository.get_document_by_name(request.object_name) is None:
            self.repository.create_document(request)
        else:
            raise ObjectNameError