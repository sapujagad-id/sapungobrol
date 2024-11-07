from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4
from loguru import logger
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import UUID, Column, Enum, Uuid, String, Text, DateTime

from document.document import DocumentType
from document.dto import DocumentCreate, DocumentFilter, DocumentUpdate

Base = declarative_base()

class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type = Column(String, nullable=False) # Enum(DocumentType)
    title = Column(String, nullable=False)
    object_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    
class DocumentRepository(ABC):
    @abstractmethod
    def get_documents(self, filter: DocumentFilter) -> list[DocumentModel]:
        pass
      
    @abstractmethod
    def get_document_by_name(self, object_name: str) -> DocumentModel:
        pass
      
    @abstractmethod
    def get_document_by_id(self, doc_id: str) -> DocumentModel:
        pass

    @abstractmethod
    def create_document(self, doc_create: DocumentCreate):
        pass

    # note: Not implemented to ensure vector database and document entries are not out of sync
    # @abstractmethod
    # def update_document(self, doc_id: str, doc_update: DocumentUpdate):
    #     pass
    
    # @abstractmethod
    # def delete_document(self, doc_id: str):
    #     pass


class PostgresDocumentRepository(DocumentRepository):
    def __init__(self, session: sessionmaker) -> None:
        self.create_session = session
        self.logger = logger.bind(service="PostgresDocumentRepository")

    def get_documents(self, filter: DocumentFilter) -> list[DocumentModel]:
        with self.create_session() as session:
            assert isinstance(session, Session)
            self.logger.debug("Fetching documents with filters: %s", filter)
            q = session.query(DocumentModel)
            if filter.get("created_after"):
                q = q.filter(DocumentModel.created_at >= filter["created_after"])
            if filter.get("created_before"):
                q = q.filter(DocumentModel.created_at <= filter["created_before"])
            if filter.get("updated_after"):
                q = q.filter(DocumentModel.updated_at >= filter["updated_after"])
            if filter.get("updated_before"):
                q = q.filter(DocumentModel.updated_at <= filter["updated_before"])
            if filter.get("object_name"):
                q = q.filter(DocumentModel.object_name == filter["object_name"])
            if filter.get("id"):
                q = q.filter(DocumentModel.object_name == filter["id"])
            # if no filter applied, then select ALL
            return q.all()
        
    def get_document_by_id(self, doc_id):
        with self.create_session() as session:
            with self.logger.catch(message=f"document with id {doc_id} not found", reraise=True):
                assert isinstance(session, Session)
                q = session.query(DocumentModel).filter(DocumentModel.id == doc_id)
                return q.first()
        
    def get_document_by_name(self, object_name):
        with self.create_session() as session:
            with self.logger.catch(message=f"document with name {object_name} not found", reraise=True):
                assert isinstance(session, Session)
                q = session.query(DocumentModel).filter(DocumentModel.object_name == object_name)
                return q.first()
        
    def create_document(self, doc_create: DocumentCreate):
        with self.create_session() as session:
            with self.logger.catch(message="create document error", reraise=True):
                doc_id = uuid4()
                doc_create.type = doc_create.type.lower()
                new_doc = DocumentModel(
                    **doc_create.model_dump(), 
                    id=doc_id, 
                )
                self.logger.info("awooga")
                session.add(new_doc)
                session.commit()
        