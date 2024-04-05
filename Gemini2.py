import streamlit as st
from PyPDF2 import PdfReader
import requests

# Function to extract text from PDF file at a URL
def get_pdf_text_from_url(pdf_url):
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()  # Raise an exception for any errors
        with open("temp_pdf.pdf", "wb") as f:
            f.write(response.content)
        return "temp_pdf.pdf"
    except Exception as e:
        st.error(f"An error occurred while fetching or processing the PDF from URL: {str(e)}")
        return ""

# Main function for PDF chat functionality
def main():
    st.title("Chat with PDF")
    st.sidebar.title("Options")
    option = st.sidebar.radio("Choose an Option", ("Upload PDF File", "Provide PDF URL"))

    if option == "Upload PDF File":
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

        if uploaded_file:
            st.success("PDF file uploaded successfully!")
            user_question = st.text_input("Ask a question")

            with st.form(key="chat_form"):
                chat_button_clicked = st.form_submit_button("Chat")
                if chat_button_clicked and user_question:
                    # Process the user's question and generate a response
                    # Call your chat function here with the PDF file and user_question
                    st.write("You:", user_question)
                    st.write("Chat functionality will be implemented here.")

    elif option == "Provide PDF URL":
        pdf_url = st.text_input("Enter the URL of the PDF")

        with st.form(key="pdf_form"):
            fetch_button_clicked = st.form_submit_button("Fetch PDF from URL")
            if fetch_button_clicked and pdf_url:
                pdf_file = get_pdf_text_from_url(pdf_url)
                if pdf_file:
                    st.success("PDF loaded successfully!")
                    user_question = st.text_input("Ask a question")

                    with st.form(key="chat_form"):
                        chat_button_clicked = st.form_submit_button("Chat")
                        if chat_button_clicked and user_question:
                            # Process the user's question and generate a response
                            # Call your chat function here with the PDF file and user_question
                            st.write("You:", user_question)
                            st.write("Chat functionality will be implemented here.")

if __name__ == "__main__":
    main()
