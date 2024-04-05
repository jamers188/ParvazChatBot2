import streamlit as st
import os
import json
from streamlit_lottie import st_lottie
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
import requests
from PyPDF2 import PdfReader

# Load environment variables from .env file if present
load_dotenv()

API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Function to load Gemini Pro model and start chat
def load_model():
    model = genai.ChatSession("gemini-pro")
    return model

# Function to process PDF URL input and generate a response
def process_pdf_url(pdf_url, chat):
    try:
        # Download PDF from URL
        response = requests.get(pdf_url)
        if response.status_code == 200:
            pdf_content = BytesIO(response.content)
            raw_text = get_pdf_text(pdf_content)
            st.success("PDF processed successfully.")
            st.write("Chat with the PDF:")
            response = chat.generate_text(raw_text)
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
def get_pdf_text(pdf_content):
    raw_text = ""
    pdf_reader = PdfReader(pdf_content)
    for page in pdf_reader.pages:
        raw_text += page.extract_text()
    return raw_text

# Main function
def main():
    # Initialize session state
    if 'pdf_history' not in st.session_state:
        st.session_state['pdf_history'] = []
    if 'pdf_srchistory' not in st.session_state:
        st.session_state['pdf_srchistory'] = []

    # Set page configuration
    st.set_page_config(page_title="MyAI", page_icon="🤖")

    # Load model
    chat = load_model()

    # Define selected option
    selected_option = st.sidebar.selectbox("Select an Option", ["HOME", "Prompt Chat", "IMAGE CHAT", "PDF CHAT", "CHAT HISTORY"])

    # Displaying the PDF chat interface
    if selected_option == "PDF CHAT":
        st.title("PDF CHAT")
        # Option to choose between file upload and URL input
        pdf_option = st.radio("Choose an option", ["Upload PDF", "Input PDF URL"])
        if pdf_option == "Upload PDF":
            uploaded_pdfs = st.file_uploader("Upload PDF(s)", accept_multiple_files=True)
            if uploaded_pdfs:
                # Process uploaded PDFs
                for pdf_file in uploaded_pdfs:
                    process_pdf_upload(pdf_file, chat)
        elif pdf_option == "Input PDF URL":
            pdf_url = st.text_input("Enter PDF URL")
            if pdf_url:
                # Process PDF URL
                process_pdf_url(pdf_url, chat)

# Function to process PDF upload and generate a response
def process_pdf_upload(pdf_file, chat):
    try:
        with st.spinner("Processing..."):
            raw_text = get_pdf_text(pdf_file)
            st.success("PDF processed successfully.")
            st.write("Chat with the PDF:")
            response = chat.generate_text(raw_text)
            if response:
                st.session_state['pdf_history'].append(("Bot", response.text))
                st.success("Response:")
                st.write(response.text)
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")

# Call the main function when the script is executed
if __name__ == "__main__":
    main()
