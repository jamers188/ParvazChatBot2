import streamlit as st
import os
import json
from streamlit_lottie import st_lottie
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
import requests
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PIL import Image
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from streamlit_option_menu import option_menu

# Load environment variables from .env file if present
load_dotenv()

API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

# Initialize the Gemini Pro model and start the chat
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

# Initialize Streamlit app
st.set_page_config(page_title="MyAI", page_icon='🤖')

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# Define function to get responses from the Gemini chatbot
def get_gemini_response(question):
    try:
        response = chat.send_message(question, stream=True)
        return response
    except generation_types.BlockedPromptException as e:
        st.error("Sorry, the provided prompt triggered a content filter. Please try again with a different prompt.")


# Define function to display chat history
def display_chat_history():
    st.title("Chat History")
    if st.session_state['chat_history']:
        for role, text in st.session_state['chat_history']:
            if role == "YOU":
                st.markdown(f"**{role} 👤**: {text} ")
            elif role == "TEXT_BOT":
                st.markdown(f"**{role} 🤖**: {text} ")
    else:
        st.error("Chat History is empty. Start asking questions to build the history.")

# Define function to chat with the Gemini chatbot
def chat_with_gemini():
    input_text = st.text_input("Ask your Question")
    if input_text:
        response = get_gemini_response(input_text)
        if response:
            st.session_state['chat_history'].append(("YOU", input_text))
            st.success("The Response is")

            if hasattr(response, 'text'):
                st.write(response.text)
                st.session_state['chat_history'].append(("TEXT_BOT", response.text))
            elif hasattr(response, 'parts'):
                for part in response.parts:
                    if hasattr(part, 'text') and part.text:
                        text_line = part.text
                        st.write(text_line)
                        st.session_state['chat_history'].append(("TEXT_BOT", text_line))
                    elif hasattr(part, 'candidates') and part.candidates:
                        for candidate in part.candidates:
                            if hasattr(candidate, 'content') and candidate.content:
                                text_line = candidate.content.text
                                st.write(text_line)
                                st.session_state['chat_history'].append(("TEXT_BOT", text_line))
                            else:
                                st.warning("Invalid response format. Unable to extract text from candidates.")
                    else:
                        st.warning("Invalid response format. Unable to extract text from parts.")
            else:
                st.error("Error: Invalid response format.")
        else:
            st.error("Error: Failed to retrieve response from the chat service.")

# Define function to extract text from a PDF file

# Define function to chat about a PDF
def chat_about_pdf(pdf_text):
    input_text = st.text_input("Ask about the PDF")
    if st.button("Send"):
        if input_text:
            response = get_gemini_response(input_text)
            if response:
                st.session_state['chat_history'].append(("YOU", input_text))
                st.session_state['chat_history'].append(("TEXT_BOT", response.text))

# Define main function
def main():
    selected = option_menu(
        menu_title=None,
        options=["HOME", "Prompt Chat", "IMAGE CHAT", "PDF CHAT", "CHAT HISTORY"],
        icons=['house', "pen", 'image', 'book', 'chat', 'person'],
        default_index=0,
        menu_icon='user',
        orientation="horizontal",
        styles="""
        <style>
            .option-menu {
                width: 200px;
                margin-right: 20px;
            }
        </style>
    """
    )

    if selected == "HOME":
        # Display home page content
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

    elif selected == "Prompt Chat":
        chat_with_gemini()

    elif selected == "IMAGE CHAT":
        pass  # Placeholder for image chat functionality

    elif selected == "PDF CHAT":
        st.subheader("Upload PDF or Paste URL")
        upload_file = st.file_uploader("Upload PDF File", type=['pdf'])
        pdf_url = st.text_input("Paste PDF URL")

        if upload_file:
            pdf_docs = [upload_file]
        elif pdf_url:
            try:
                response = requests.get(pdf_url)
                if response.status_code == 200:
                    pdf_bytes = BytesIO(response.content)
                    pdf_docs = [pdf_bytes]
                else:
                    st.error(f"Failed to retrieve PDF from URL. Status code: {response.status_code}")
            except Exception as e:
                st.error(f"Error loading PDF from URL: {str(e)}")
                pdf_docs = []

        if pdf_docs:
            pdf_text = ""
            for pdf in pdf_docs:
                pdf_text += extract_text_from_pdf(pdf)

            if pdf_text:
                st.write(pdf_text)
                chat_about_pdf(pdf_text)
            else:
                st.error("No text extracted from PDF.")

    elif selected == "CHAT HISTORY":
        display_chat_history()

if __name__ == "__main__":
    main()
