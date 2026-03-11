import argparse
import json
import sys
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
import os
from dotenv import load_dotenv

load_dotenv()

def process_query(query: str):
    try:
        # Initialize components
        embeddings = OpenAIEmbeddings()
        
        # Load the vector store
        vector_store_path = "data/vector_store"
        if not os.path.exists(vector_store_path):
            print(json.dumps({
                "error": "Vector store not found",
                "sources": []
            }))
            sys.exit(1)
            
        vector_store = FAISS.load_local(vector_store_path, embeddings)
        
        # Perform similarity search
        docs = vector_store.similarity_search(query, k=3)
        
        # Format results
        sources = [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown")
            }
            for doc in docs
        ]
        
        # Return results as JSON
        print(json.dumps({
            "context": "\n".join([doc.page_content for doc in docs]),
            "sources": sources
        }))
        
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "sources": []
        }))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, required=True)
    args = parser.parse_args()
    
    process_query(args.query)