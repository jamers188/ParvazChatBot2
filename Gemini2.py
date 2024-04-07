import streamlit as st
import os
from PyPDF2 import PdfReader
from io import BytesIO
import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from google.generativeai.types import generation_types

# Load environment variables from .env file if present
load_dotenv()

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

# Function to fetch PDF content from URL
def fetch_pdf_content(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            pdf_bytes = BytesIO(response.content)
            pdf_reader = PdfReader(pdf_bytes)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        else:
            st.error(f"Failed to retrieve PDF from URL. Status code: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error fetching PDF content from URL: {str(e)}")
        return None

# Function to split text into smaller chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

# Function to create vector store from text chunks
def get_vector_store(text_chunks):
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local("faiss_index")
        return vector_store  # Return the created vector store
    except Exception as e:
        st.error(f"Error creating vector store: {str(e)}")
        return None

# Function to load and configure the conversational chain
def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain

# Main function for PDF chat functionality
def main1():
    st.header("Chat with PDF")

    user_question = st.chat_input("Ask a Question from the PDF Files")

    if user_question:
        user_input(user_question)

    st.title("Menu:")
    option = st.radio("Choose an option", ["Upload PDF Files", "Paste PDF URL"])

    if option == "Upload PDF Files":
        pdf_docs = st.file_uploader("Upload your PDF Files and Click on the Submit & Process Button", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                pdf_docs = [pdf for pdf in pdf_docs if pdf.name.endswith('.pdf')]
                if not pdf_docs:
                    st.error("Please upload PDF files only.")
                    return
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                vector_store = get_vector_store(text_chunks)
                process_pdf_content(vector_store)  # Pass the vector store to the process_pdf_content function

    elif option == "Paste PDF URL":
        pdf_url = st.text_input("Paste PDF URL here:")
        if pdf_url:
            raw_text = fetch_pdf_content(pdf_url)
            if raw_text:
                text_chunks = get_text_chunks(raw_text)
                vector_store = get_vector_store(text_chunks)
                process_pdf_content(vector_store)  # Pass the vector store to the process_pdf_content function

# Function to process PDF content
def process_pdf_content(vector_store):
    if vector_store:
        st.success("Done")
        st.balloons()
        # Here you can use the vector store for further processing
    else:
        st.error("Failed to process PDF content")

# Function to process user input and generate a response
def user_input(user_question):
    try:
        # Load or define new_db if not already loaded
        if 'new_db' not in st.session_state:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            st.session_state['new_db'] = new_db
        
        docs = st.session_state['new_db'].similarity_search(user_question)
        chain = get_conversational_chain()
        response1 = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        st.write("Reply: ", response1["output_text"])
        st.session_state["pdf_history"].append(("YOU", user_question))
        st.session_state["pdf_history"].append(("PDF_BOT", response1["output_text"]))
    except Exception as e:
        st.error(f"An error occurred while processing the question: {str(e)}")

# Initialize session state for PDF chat history
if 'pdf_history' not in st.session_state:
    st.session_state['pdf_history'] = []

if __name__ == "__main__":
    main1()
