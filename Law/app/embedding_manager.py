from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from typing import List, Optional
import os
import logging

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self, vector_store_path: str = "data/vector_store"):
        self.vector_store_path = vector_store_path
        self.embeddings = OpenAIEmbeddings()

    def create_or_load_vector_store(self, documents: Optional[List[Document]] = None):
        """Create new vector store or load existing one"""
        try:
            if documents:
                logger.info("Creating new vector store")
                vector_store = FAISS.from_documents(documents, self.embeddings)
                self._save_vector_store(vector_store)
                return vector_store
            elif os.path.exists(self.vector_store_path):
                logger.info("Loading existing vector store")
                return self._load_vector_store()
            else:
                logger.warning("No documents provided and no existing vector store found")
                return None
        except Exception as e:
            logger.error(f"Error with vector store: {str(e)}")
            raise

    def _save_vector_store(self, vector_store):
        """Save vector store to disk"""
        os.makedirs(self.vector_store_path, exist_ok=True)
        vector_store.save_local(self.vector_store_path)

    def _load_vector_store(self):
        """Load vector store from disk"""
        return FAISS.load_local(self.vector_store_path, self.embeddings)