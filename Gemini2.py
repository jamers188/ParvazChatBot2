import streamlit as st
import os
from io import BytesIO
import requests
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from google.generativeai.types import generation_types

# Initialize Streamlit app
st.set_page_config(page_title="MyAI", page_icon='🤖')  # Page title

# Initialize Gemini Pro model
model = ChatGoogleGenerativeAI(model="openai-gpt")

# Initialize session state for chat history and PDF history
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'pdf_history' not in st.session_state:
    st.session_state['pdf_history'] = []

# Function to get responses from the Gemini chatbot
def get_gemini_response(question):
    try:
        response = model(question)
        return response
    except generation_types.BlockedPromptException as e:
        st.error("Sorry, the provided prompt triggered a content filter. Please try again with a different prompt.")

# Function to extract text from PDF documents
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
        except Exception as e:
            st.warning(f"Error reading PDF: {str(e)}")
    return text

# Function to process user input and generate a response
def process_user_input():
    user_question = st.text_input("Ask a question")
    if st.button("Ask") and user_question:
        response = get_gemini_response(user_question)
        if response:
            st.session_state['chat_history'].append(("You", user_question))
            st.session_state['chat_history'].append(("Bot", response.text))
            st.success("Response:")
            st.write(response.text)

# Function to process PDF upload and generate a response
def process_pdf_upload(pdf_docs):
    if st.button("Submit & Process"):
        with st.spinner("Processing..."):
            raw_text = get_pdf_text(pdf_docs)
            st.success("PDF processed successfully.")
            st.write("Extracted Text:")
            st.write(raw_text)
            response = get_gemini_response(raw_text)
            if response:
                st.session_state['pdf_history'].append(("PDF Uploaded", "Yes"))
                st.session_state['pdf_history'].append(("Bot", response.text))
                st.success("Response:")
                st.write(response.text)

# Display chat interface for text
st.title("Chat with Gemini Pro")
process_user_input()

# Display chat history for text
st.title("Text Chat History")
for role, text in st.session_state['chat_history']:
    st.markdown(f"**{role}:** {text}")

# Display chat interface for PDFs
st.title("Chat with PDF")
pdf_docs = st.file_uploader("Upload PDF(s)", accept_multiple_files=True)
if pdf_docs:
    process_pdf_upload(pdf_docs)

# Display chat history for PDFs
st.title("PDF Chat History")
for role, text in st.session_state['pdf_history']:
    st.markdown(f"**{role}:** {text}")
