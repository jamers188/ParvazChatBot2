import streamlit as st
import os
import json
from streamlit_lottie import st_lottie
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
import requests
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PIL import Image
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

## function to load Gemini Pro model and get responses
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

from streamlit_option_menu import option_menu
 #initialize our streamlit app
st.set_page_config(page_title="MyAI", page_icon='🤖')  # page title

# Function to load and configure the conversational chain
def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """

    model = ChatGoogleGenerativeAI(model="gemini-pro",temperature=0.3)

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain

# Function to process user input and generate a response
# Function to process user input and generate a response
def user_input(user_question, docs):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    try:
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        chain = get_conversational_chain()

        response1 = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)

        output_Text = response1["output_text"]
        st.write("Reply: ", output_Text)
        st.session_state["pdf_history"].append(("YOU", user_question))
        st.session_state["pdf_history"].append(("PDF_BOT", output_Text))
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

    user_question = st.chat_input("Ask a Question from the PDF Files")

    if user_question:
        user_input(user_question)
        #st.session_state['pdf_history'].append(("YOU", user_question))

    st.title("Menu:")
    st.sidebar.header("Options")
    option = st.sidebar.radio("Choose an Option", ("Upload PDF Files", "Provide PDF URL"))

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
                get_vector_store(text_chunks)
                st.success("Done")
                pdf_names = [pdf.name for pdf in pdf_docs]
                st.session_state["pdf_srchistory"].append(("PDFS UPLOADED", pdf_names))
                st.balloons()

    elif option == "Provide PDF URL":
        pdf_url = st.text_input("Enter the URL of the PDF")
        if st.button("Chat with PDF from URL"):
            with st.spinner("Fetching PDF from URL..."):
                pdf_text = get_pdf_text_from_url(pdf_url)
                if pdf_text:
                    user_question = st.text_input("Ask a Question from the PDF")
                    if st.button("Ask"):
                        if user_question:
                            user_input(user_question, [pdf_text])  # Pass pdf_text as docs
                        else:
                            st.warning("Please enter a question.")
                else:
                    st.error("Failed to fetch PDF from the provided URL.")


# Main block to run the app
if __name__ == "__main__":
    main1()
