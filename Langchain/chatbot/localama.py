from langchain_community.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.llms import Ollama

import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

# Prompt Template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. Please respond to the user's question in a concise manner."),
        ("user", "Question: {question}"),
    ]
)

# Streamlit app
st.title("LangChain OpenAI Chatbot")
input_text = st.text_input("Enter your question here", placeholder="What is LangChain?")

# OpenAI LLM
llm = Ollama(
    model="llama3.1:8b",
    temperature=0.7,
    max_tokens=1000,
)

# Output parser
output_parser = StrOutputParser()
chain = prompt | llm | output_parser