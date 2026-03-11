from typing import List
try:
    from langchain_community.document_loaders import PyMuPDFLoader
except ImportError:
    try:
        from langchain.document_loaders import PyMuPDFLoader
    except ImportError:
        raise ImportError("Could not import PyMuPDFLoader. Please install langchain-community")

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import logging


logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def process_pdf(self, pdf_path: str) -> List[Document]:
        """Process PDF file and return chunks"""
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            loader = PyMuPDFLoader(pdf_path)
            documents = loader.load()
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Created {len(chunks)} chunks from PDF")
            return chunks
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise