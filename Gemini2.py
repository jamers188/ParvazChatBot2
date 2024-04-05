import streamlit as st
import os
import requests
from PyPDF2 import PdfReader

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
        pdf_reader = PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text()
    return text

# Main function for PDF chat functionality
def main():
    st.header("Chat with PDF from URL")

    pdf_url = st.text_input("Enter PDF URL:")
    
    if st.button("Process PDF from URL"):
        with st.spinner("Processing..."):
            pdf_file = download_pdf_from_url(pdf_url)
            if pdf_file:
                raw_text = get_pdf_text(pdf_file)
                st.write("Extracted Text:")
                st.write(raw_text)
                st.success("Processing complete")
            else:
                st.error("Failed to download PDF from the provided URL")

if __name__ == "__main__":
    main()
