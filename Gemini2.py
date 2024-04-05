import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests
from io import BytesIO
from PyPDF2 import PdfReader

# Load environment variables from .env file if present
load_dotenv()

API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Main function
def main():
    # Set page configuration
    st.set_page_config(page_title="MyAI", page_icon="🤖")

    # Define selected option
    selected_option = st.sidebar.selectbox("Select an Option", ["HOME", "PDF CHAT"])

    # Displaying the PDF chat interface
    if selected_option == "PDF CHAT":
        st.title("PDF CHAT")
        # Option to input PDF URL
        pdf_url = st.text_input("Enter PDF URL")
        if pdf_url:
            # Process PDF URL
            process_pdf_url(pdf_url)

# Function to process PDF URL input and generate a response
def process_pdf_url(pdf_url):
    try:
        # Download PDF from URL
        response = requests.get(pdf_url)
        if response.status_code == 200:
            pdf_content = BytesIO(response.content)
            raw_text = get_pdf_text(pdf_content)
            st.success("PDF processed successfully.")
            st.write("Chat with the PDF:")
            # Chat with the PDF using GenerativeAI
            model = genai.GenerativeModel("gemini-pro")
            chat_session = model.start_chat(history=raw_text)
            response = chat_session.query("Hello")
            if response:
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

# Call the main function when the script is executed
if __name__ == "__main__":
    main()
