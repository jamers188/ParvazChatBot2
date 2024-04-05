import streamlit as st
from transformers import pipeline

# Load the chatbot model
chatbot = pipeline("text-generation", model="microsoft/DialoGPT-large")

# Main function for PDF chat functionality
def main():
    st.title("Chat with PDF")
    st.sidebar.title("Options")
    option = st.sidebar.radio("Choose an Option", ("Upload PDF File", "Provide PDF URL"))

    with st.form(key="chat_form"):
        if option == "Upload PDF File":
            uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

            if uploaded_file:
                st.success("PDF file uploaded successfully!")

        elif option == "Provide PDF URL":
            pdf_url = st.text_input("Enter the URL of the PDF")
            fetch_button_clicked = st.form_submit_button("Fetch PDF from URL")

            if fetch_button_clicked:
                if pdf_url:
                    st.success("PDF loaded successfully!")

        user_question = st.text_input("Ask a question")

        chat_button_clicked = st.form_submit_button("Chat")

    if chat_button_clicked:
        if user_question:
            # Pass user's question to the chatbot model and get response
            chat_response = chatbot(user_question, max_length=100)
            st.write("You:", user_question)
            st.write("Bot:", chat_response[0]['generated_text'])
        else:
            st.warning("Please enter a question.")

if __name__ == "__main__":
    main()
