import streamlit as st
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from google.generativeai.types import generation_types
import requests
from io import BytesIO

# Load environment variables from .env file if present
load_dotenv()

API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

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

# Function to process user input and generate a response
# Function to process user input and generate a response
def user_input(user_question, docs):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    try:
        if os.path.exists("faiss_index/index.faiss"):
            new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            chain = get_conversational_chain()

            response1 = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)

            output_text = response1["output_text"]
            st.write("Reply: ", output_text)
            st.session_state["pdf_history"].append(("YOU", user_question))
            st.session_state["pdf_history"].append(("PDF_BOT", output_text))
        else:
            st.error("FAISS index file not found. Please create the index first.")
    except Exception as e:
        st.error(f"An error occurred while processing the question: {str(e)}")
        # If an error occurs, ensure to display the user's question
        st.session_state["pdf_history"].append(("YOU", user_question))


# Function to get PDF text from URL
def get_pdf_text_from_url(pdf_url):
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()  # Raise an exception for any errors
        with BytesIO(response.content) as file:
            pdf_reader = PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        st.error(f"An error occurred while fetching or processing the PDF from URL: {str(e)}")

# Main function for PDF chat functionality
def main1():
    st.header("Chat with PDF ")

    user_question = st.text_input("Ask a Question from the PDF", key="pdf_question_input")

    st.title("Menu:")
    st.sidebar.header("Options")
    option = st.sidebar.radio("Choose an Option", ("Upload PDF Files", "Provide PDF URL"))

    if option == "Upload PDF Files":
        # Add code for uploading PDF files here
        pass

    elif option == "Provide PDF URL":
        pdf_url = st.text_input("Enter the URL of the PDF", key="pdf_url_input")
        if st.button("Chat with PDF from URL", key="pdf_chat_button"):
            with st.spinner("Fetching PDF from URL..."):
                pdf_text = get_pdf_text_from_url(pdf_url)
                if pdf_text:
                    if user_question:
                        # Add the user's question to the chat history
                        st.session_state['pdf_history'].append(("YOU", user_question))

                        # Process the user's question and generate a response
                        user_input(user_question, [pdf_text])
                    else:
                        st.warning("Please enter a question.")
                else:
                    st.error("Failed to fetch PDF from the provided URL.")

# Main block to run the app
if __name__ == "__main__":
    # Initialize session state for chat history if it doesn't exist
    if 'pdf_history' not in st.session_state:
        st.session_state['pdf_history'] = []

    main1()
