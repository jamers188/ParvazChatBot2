import streamlit as st
import os
import json
from io import BytesIO
import requests
from PyPDF2 import PdfReader

# Load environment variables from .env file if present
from dotenv import load_dotenv
load_dotenv()

# Import the GenerativeModel for interaction with Google Generative AI API
import google.generativeai as genai

# Configure Google Generative AI API
API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Define the main function
def main():
    # Set page configuration
    st.set_page_config(page_title="MyAI", page_icon="🤖")

    # Define selected option
    selected_option = st.sidebar.selectbox("Select an Option", ["HOME", "PDF CHAT"])

    # Displaying the home page content
    if selected_option == "HOME":
        st.title("Welcome to MyAI")
        st.write("This is the home page content.")

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
            st.write("PDF content goes here")  # Placeholder, replace with actual interaction with the content
            # You can call your generative model here if you want to generate a response based on the PDF content

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
                    st.write("PDF content goes here")  # Placeholder, replace with actual interaction with the content
                    # You can call your generative model here if you want to generate a response based on the PDF content
                else:
                    st.error(f"Failed to retrieve PDF from URL. Status code: {response.status_code}")
            except Exception as e:
                st.error(f"Error processing PDF from URL: {str(e)}")

# Function to extract text from PDF files
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
