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

# Load the chat model
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

# Define the main function
def main():
    # Initialize session state for chat history, image history, PDF history, etc.
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    # Set page configuration
    st.set_page_config(page_title="MyAI", page_icon="🤖")

    # Define selected option
    selected_option = st.sidebar.selectbox("Select an Option", ["HOME", "PDF CHAT"])

    # Displaying the home page content
    if selected_option == "HOME":
        st.markdown("""# <span style='color:#0A2647'> Welcome to My Streamlit App  ** MyAI 🦅</span>""", unsafe_allow_html=True)
        st.markdown("""#### <span style='color:#0E6363'> Based on Gemini-PRO, GEMINI-PRO-Vision LLM API FROM GOOGLE</span>""", unsafe_allow_html=True)
        st.markdown("""## <span style='color:##11009E'>Introduction</span>""", unsafe_allow_html=True)
        st.markdown(""" <span style='color:#020C0C'> MyAI is an innovative chatbot application designed to provide intelligent responses to your queries. Powered by advanced language and vision models, it offers a seamless conversational experience for various use cases. </span>""", unsafe_allow_html=True)
        st.markdown("""
        ### <span style='color:#0F0F0F'>Instructions:</span>
        <span style='color:#222831'>  📁 Navigate to PDF CHAT to chat with the PDF's.</span>
        <br>
        """, unsafe_allow_html=True)

    # Displaying the PDF chat interface
    elif selected_option == "PDF CHAT":
        st.title("PDF CHAT")
        # Input PDF URL
        pdf_url = st.text_input("Enter PDF URL")
        if pdf_url:
            # Process PDF URL
            process_pdf_url(pdf_url)

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
                    response = chat.send_message(raw_text, stream=True)
                    if response:
                        st.success("Response:")
                        st.write(response.text)
                else:
                    st.error(f"Failed to retrieve PDF from URL. Status code: {response.status_code}")
            except Exception as e:
                st.error(f"Error processing PDF from URL: {str(e)}")

# Function to extract PDF text
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
