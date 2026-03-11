from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate
import logging

logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.llm = ChatOpenAI(model_name="gpt-4", temperature=0.7)
        
        self.prompt_template = """You are a constitutional law expert assistant. 
        Use the following pieces of context to provide a detailed and comprehensive answer to the question. 
        Include specific references to relevant sections and articles when possible.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.

        Context: {context}

        Question: {question}

        Answer: """

        self.PROMPT = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )

        self.qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 5}  # Increase number of retrieved documents
            ),
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": self.PROMPT}
        )

    def query(self, question: str, chat_history: list = [], return_docs: int = 5):
        """Process a question and return answer with sources"""
        try:
            result = self.qa_chain({"question": question, "chat_history": chat_history})
            return {
                "answer": result["answer"],
                "source_documents": result["source_documents"][:return_docs]
            }
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise