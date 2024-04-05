import streamlit as st
from PyPDF2 import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI

# Initialize Streamlit app
st.set_page_config(page_title="PDF Chat", page_icon='📄')

# Initialize Gemini Pro model
model = ChatGoogleGenerativeAI(model="openai-gpt")

# Initialize session state for PDF history
if 'pdf_history' not in st.session_state:
    st.session_state['pdf_history'] = []

# Function to extract text from PDF documents
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
        except Exception as e:
            st.warning(f"Error reading PDF: {str(e)}")
    return text

# Function to process PDF upload and generate a response
def process_pdf_upload(pdf_docs):
    if st.button("Submit & Process"):
        with st.spinner("Processing..."):
            raw_text = get_pdf_text(pdf_docs)
            st.success("PDF processed successfully.")
            st.write("Extracted Text:")
            st.write(raw_text)
            response = model(raw_text)
            if response:
                st.session_state['pdf_history'].append(("PDF Uploaded", "Yes"))
                st.session_state['pdf_history'].append(("Bot", response.text))
                st.success("Response:")
                st.write(response.text)

# Display PDF upload interface
st.title("Chat with PDF")
pdf_docs = st.file_uploader("Upload PDF(s)", accept_multiple_files=True)
if pdf_docs:
    process_pdf_upload(pdf_docs)

# Display PDF chat history
st.title("PDF Chat History")
for role, text in st.session_state['pdf_history']:
    st.markdown(f"**{role}:** {text}")
