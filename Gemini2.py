import streamlit as st
import os
from io import BytesIO
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load environment variables from .env file if present
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Function to extract text from PDF documents
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            # Check file size before reading
            if pdf.size > 200 * 1024 * 1024:  # 200 MB in bytes
                st.warning(f"Skipping file: {pdf.name}. File size exceeds 200 MB.")
                continue
        
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
        except Exception as e:
            if type(e).__name__ == "PdfReadError":
                st.warning(f"Skipping non-PDF file: {pdf.name}. Error: {str(e)}")
                continue
            else:
                raise  # Raise the exception if it's not a PdfReadError
    return text

# Function to split text into smaller chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

# Function to load and configure the conversational chain
def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context. If the answer is not available in the context, say "answer is not available in the context".
    
    Context:
    {context}?
    
    Question:
    {question}
    
    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

# Main function for PDF chat functionality
def main():
    st.header("Chat with PDF")

    user_question = st.text_input("Ask a question about the PDF content")

    st.title("Upload your PDF Files")
    pdf_docs = st.file_uploader("Choose PDF Files", accept_multiple_files=True)
    
    if st.button("Submit & Process") and pdf_docs:
        with st.spinner("Processing..."):
            pdf_docs = [pdf for pdf in pdf_docs if pdf.name.endswith('.pdf')]
            if not pdf_docs:
                st.error("Please upload PDF files only.")
                return

            # Extract text from PDFs
            raw_text = get_pdf_text(pdf_docs)
            text_chunks = get_text_chunks(raw_text)

            # Create vector store
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
                vector_store.save_local("faiss_index")
            except Exception as e:
                st.error("An error occurred while creating the vector store.")

            # Get user input
            try:
                new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
                docs = new_db.similarity_search(user_question)
                chain = get_conversational_chain()
                response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
                st.write("Reply: ", response["output_text"])
            except Exception as e:
                st.error(f"An error occurred while processing the question: {str(e)}")

if __name__ == "__main__":
    main()
