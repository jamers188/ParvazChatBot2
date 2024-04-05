import streamlit as st
import os
import requests
from PyPDF2 import PdfFileReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Initialize streamlit app
st.set_page_config(page_title="MyAI", page_icon='🤖')

# Function to download PDF from URL
def download_pdf_from_url(pdf_url):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        with open("temp_pdf.pdf", "wb") as f:
            f.write(response.content)
        return "temp_pdf.pdf"
    else:
        return None

# Function to extract text from PDF documents
def get_pdf_text(pdf_file):
    text = ""
    with open(pdf_file, "rb") as file:
        pdf_reader = PdfFileReader(file)
        for page_num in range(pdf_reader.getNumPages()):
            text += pdf_reader.getPage(page_num).extract_text()
    return text

# Function to split text into smaller chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

# Function to create a vector store from text chunks
def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")

# Main function for PDF chat functionality
def main():
    st.header("Chat with PDF from URL")

    pdf_url = st.text_input("Enter PDF URL:")
    
    if st.button("Process PDF from URL"):
        with st.spinner("Processing..."):
            pdf_file = download_pdf_from_url(pdf_url)
            if pdf_file:
                raw_text = get_pdf_text(pdf_file)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Processing complete")
            else:
                st.error("Failed to download PDF from the provided URL")

if __name__ == "__main__":
    main()
