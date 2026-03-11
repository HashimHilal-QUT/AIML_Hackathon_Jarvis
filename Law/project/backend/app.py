from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import openai
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_rag_context(query):
    try:
        # Initialize components
        embeddings = OpenAIEmbeddings()
        
        # Load the vector store
        vector_store_path = "../data/vector_store"
        if not os.path.exists(vector_store_path):
            return {
                "error": "Vector store not found",
                "context": "",
                "sources": []
            }
            
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
        
        context = "\n".join([doc.page_content for doc in docs])
        
        return {
            "context": context,
            "sources": sources
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "context": "",
            "sources": []
        }

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({"error": "No messages provided"}), 400
        
        latest_message = messages[-1]['content']
        
        # Get RAG context
        rag_results = get_rag_context(latest_message)
        
        if "error" in rag_results and rag_results["error"]:
            print(f"RAG Error: {rag_results['error']}")
        
        # Create system message with RAG context
        system_message = {
            "role": "system",
            "content": f"You are a legal assistant. Use the following context to answer questions: {rag_results.get('context', '')}"
        }
        
        # Create OpenAI chat completion
        completion = openai.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4'),
            messages=[system_message] + messages,
            temperature=0.7
        )
        
        return jsonify({
            "message": completion.choices[0].message.content,
            "sources": rag_results.get('sources', [])
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)