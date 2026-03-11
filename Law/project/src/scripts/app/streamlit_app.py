import streamlit as st
import os
from pathlib import Path
from document_processor import DocumentProcessor
from embedding_manager import EmbeddingManager
from rag_pipeline import RAGPipeline
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConstitutionalRAGApp:
    def __init__(self):
        self.setup_environment()
        self.initialize_session_state()
        self.setup_ui()
        
    def setup_environment(self):
        """Setup environment variables and configurations"""
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OpenAI API key not found. Please check your .env file.")
            st.stop()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "rag_pipeline" not in st.session_state:
            st.session_state.rag_pipeline = None
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

    def setup_ui(self):
        """Setup the Streamlit UI"""
        st.title("Constitutional Law Assistant")
        
        # Sidebar
        with st.sidebar:
            st.title("Constitutional Law Assistant")
            st.markdown("---")
            
            # File uploader
            uploaded_file = st.file_uploader(
                "Upload Constitutional Document",
                type=["pdf"],
                help="Upload the constitutional document you want to analyze"
            )
            
            if uploaded_file:
                with st.spinner("Processing document..."):
                    self.process_uploaded_file(uploaded_file)
            
            st.markdown("---")
            st.markdown("### About")
            st.markdown("""
            This AI assistant helps you understand constitutional law concepts.
            
            **Features:**
            - Document Analysis
            - Contextual Responses
            - Source Citations
            """)
        
        # Initialize RAG pipeline if not already done
        if "rag_pipeline" not in st.session_state or st.session_state.rag_pipeline is None:
            if not uploaded_file:
                st.info("Please upload a constitutional document to begin.")
                return
        
        for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                        if "sources" in message:
                            with st.expander("📚 View Sources", expanded=False):
                                st.markdown(message["sources"], unsafe_allow_html=True)

        # Update the RAG pipeline response handling
        if prompt := st.chat_input("Ask about the constitution..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                sources_placeholder = st.empty()
                
                try:
                    # Increase the number of returned documents
                    result = st.session_state.rag_pipeline.query(
                        prompt,
                        return_docs=5  # Increase number of source documents
                    )
                    response = result["answer"]
                    sources = self.format_sources(result["source_documents"])
                    
                    message_placeholder.markdown(response)
                    with sources_placeholder.expander("📚 View Sources", expanded=False):
                        st.markdown(sources, unsafe_allow_html=True)
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "sources": sources
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing query: {str(e)}")
                    message_placeholder.error("I apologize, but I encountered an error. Please try again.")

    def process_uploaded_file(self, uploaded_file):
        """Process uploaded PDF file"""
        try:
            # Save uploaded file temporarily
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Initialize components
            doc_processor = DocumentProcessor()
            embedding_manager = EmbeddingManager()
            
            # Process document
            chunks = doc_processor.process_pdf(temp_path)
            if not chunks:
                st.error("No content could be extracted from the PDF.")
                return
            
            # Create vector store
            vector_store = embedding_manager.create_or_load_vector_store(chunks)
            
            # Initialize RAG pipeline
            st.session_state.rag_pipeline = RAGPipeline(vector_store)
            st.success("Document processed successfully!")
            
            # Cleanup
            os.remove(temp_path)
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            st.error("Error processing the document. Please try again.")
    
    def format_sources(self, source_documents):
        """Format source documents for display with full content"""
        sources_text = ""
        for i, doc in enumerate(source_documents, 1):
            # Show full content instead of just preview
            content = doc.page_content
            # Add metadata if available
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            page_num = metadata.get('page', 'N/A')
            
            sources_text += f"""
                    ### Source {i} (Page {page_num})

                    <details>
                    <summary>Click to view full content</summary>

                    {content}

                    </details>

                    ---
                    """
        return sources_text
def add_custom_css():
    st.markdown("""
        <style>
        .stMarkdown details {
            margin: 10px 0;
            padding: 10px;
            background-color: rgba(247, 247, 247, 0.1);
            border-radius: 5px;
        }
        .stMarkdown summary {
            cursor: pointer;
            padding: 5px;
            font-weight: bold;
            color: #0066cc;
        }
        .stMarkdown details[open] summary {
            margin-bottom: 10px;
            border-bottom: 1px solid #ddd;
        }
        .source-content {
            padding: 10px;
            margin-top: 5px;
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    
if __name__ == "__main__":
    st.set_page_config(
        page_title="Constitutional Law Assistant",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    app = ConstitutionalRAGApp()