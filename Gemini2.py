import streamlit as st
import os
import requests
from PyPDF2 import PdfFileReader
from langchain.google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate

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

# Main function for PDF chat functionality
def main():
    st.header("Chat with PDF from URL")

    pdf_url = st.text_input("Enter PDF URL:")
    
    if st.button("Process PDF from URL"):
        with st.spinner("Processing..."):
            pdf_file = download_pdf_from_url(pdf_url)
            if pdf_file:
                # Load chat model
                chat_model = ChatGoogleGenerativeAI(model="gemini-pro")
                chat = chat_model.start_chat(history=[])

                # Load conversational chain for question answering
                chain = load_qa_chain(chat_model, chain_type="stuff", prompt=PromptTemplate())

                # Chat with the PDF content directly
                user_question = st.text_input("Ask a question about the PDF:")
                if user_question:
                    response = chain({"context": pdf_file, "question": user_question})
                    st.write("Answer:")
                    st.write(response)
            else:
                st.error("Failed to download PDF from the provided URL")

if __name__ == "__main__":
    main()
