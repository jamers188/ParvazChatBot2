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

# Define the main function
def main():
    # Initialize session state for chat history, image history, PDF history, etc.
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []
    if 'img_history' not in st.session_state:
        st.session_state['img_history'] = []
    if 'img_srchistory' not in st.session_state:
        st.session_state['img_srchistory'] = []
    if 'pdf_history' not in st.session_state:
        st.session_state['pdf_history'] = []
    if 'pdf_srchistory' not in st.session_state:
        st.session_state['pdf_srchistory'] = []

    # Set page configuration
    st.set_page_config(page_title="MyAI", page_icon="🤖")

    # Define selected option
    selected_option = st.sidebar.selectbox("Select an Option", ["HOME", "Prompt Chat", "IMAGE CHAT", "PDF CHAT", "CHAT HISTORY"])

    # Displaying the home page content
    if selected_option == "HOME":
        # Display the home page content
        st.markdown("""# <span style='color:#0A2647'> Welcome to My Streamlit App  ** MyAI 🦅</span>""", unsafe_allow_html=True)
        st.markdown("""#### <span style='color:#0E6363'> Based on Gemini-PRO, GEMINI-PRO-Vision LLM API FROM GOOGLE</span>""", unsafe_allow_html=True)
        st.markdown("""## <span style='color:##11009E'>Introduction</span>""", unsafe_allow_html=True)
        st.markdown(""" <span style='color:#020C0C'> MyAI is an innovative chatbot application designed to provide intelligent responses to your queries. Powered by advanced language and vision models, it offers a seamless conversational experience for various use cases. </span>""", unsafe_allow_html=True)
        st.markdown("""
        ### <span style='color:#0F0F0F'>Instructions:</span>
        <span style='color:#222831'>  📖 Navigate to Prompt CHAT for the Text based results..</span>
        <br>
        <span style='color:#222831'>  📸 Navigate to IMAGE CHAT for the IMAGE based results..</span>
        <br>
        <span style='color:#222831'>  📁 Navigate to PDF CHAT to chat with the PDF'S..</span>
        <br>
        <br>
         <span style='color:#222831'> Explore the Possibilities:</span>
         <br>
         
         <span style='color:#222831'> ParvazChatBot2 is a versatile tool that can assist you in various tasks, from answering questions to analyzing images and PDF documents. Explore its capabilities and discover new ways to leverage its intelligence for your needs. 
         </span>
        <br>
        """, unsafe_allow_html=True)

    # Displaying the PDF chat interface
    elif selected_option == "PDF CHAT":
        st.title("PDF CHAT")
        # Option to choose between file upload and URL input
        pdf_option = st.radio("Choose an option", ["Upload PDF", "Input PDF URL"])
        if pdf_option == "Upload PDF":
            uploaded_pdfs = st.file_uploader("Upload PDF(s)", accept_multiple_files=True)
            if uploaded_pdfs:
                # Process uploaded PDFs
                process_pdf_upload(uploaded_pdfs)
        elif pdf_option == "Input PDF URL":
            pdf_url = st.text_input("Enter PDF URL")
            if pdf_url:
                # Process PDF URL
                process_pdf_url(pdf_url)

# Function to process PDF upload and generate a response
def process_pdf_upload(pdf_files):
    if st.button("Submit & Process"):
        with st.spinner("Processing..."):
            # Process uploaded PDFs
            raw_text = get_pdf_text(pdf_files)
            st.success("PDF processed successfully.")
            st.write("Chat with the PDF:")
            response = model(raw_text)
            if response:
                st.session_state['pdf_history'].append(("PDF Uploaded", "Yes"))
                st.session_state['pdf_history'].append(("Bot", response.text))
                st.success("Response:")
                st.write(response.text)

# Function to process PDF URL input and generate a response
def process_pdf_url(pdf_url):
    if st.button("Submit & Process"):
        with st.spinner("Processing..."):
            try:
                # Download PDF from URL
                response = requests.get(pdf_url)
                if response.status_code == 200:
                    pdf_content = BytesIO(response.content)
                    raw_text = get_pdf_text([pdf_content])
                    st.success("PDF processed successfully.")
                    st.write("Chat with the PDF:")
                    response = model(raw_text)
                    if response:
                        st.session_state['pdf_srchistory'].append(("PDF URL", pdf_url))
                        st.session_state['pdf_history'].append(("Bot", response.text))
                        st.success("Response:")
                        st.write(response.text)
                else:
                    st.error(f"Failed to retrieve PDF from URL. Status code: {response.status_code}")
            except Exception as e:
                st.error(f"Error processing PDF from URL: {str(e)}")

# Function to get PDF text
def get_pdf_text(pdf_files):
    raw_text = ""
    for pdf_file in pdf_files:
        pdf_reader = PdfReader(pdf_file)
        for page in pdf_reader.pages:
            raw_text += page.extract_text()
    return raw_text

# Call the main function when the script is executed
if __name__ == "__main__":
    main()
