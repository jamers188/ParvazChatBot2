import streamlit as st
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
import requests
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
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

## function to load Gemini Pro model and get responses
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

# Use option_menu with the defined styles
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

# Initialize session state for chat history,image history,pdf history if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'img_history' not in st.session_state:
    st.session_state['img_history'] = []
if 'img_srchistory' not in st.session_state:
    st.session_state['img_srchistory'] = []
if 'pdf_history' not in st.session_state:
    st.session_state['pdf_history'] = []
if 'pdf_srchistory' not in st.session_state:
    st.session_state['pdf_srchistory'] = []

# Displaying the home page content
if selected == "HOME":
    st.markdown("# Welcome to My Streamlit App  ** MyAI 🦅**")
    st.markdown("#### Based on Gemini-PRO,GEMINI-PRO-Vision LLM API FROM GOOGLE")
    st.markdown("## Introduction")
    st.markdown("MyAI is an innovative chatbot application designed to provide intelligent responses to your queries. Powered by advanced language and vision models, it offers a seamless conversational experience for various use cases.")

    st.markdown("""
    ### Instructions:
    📖 Navigate to Prompt CHAT for the Text based results..
    📸 Navigate to IMAGE CHAT for the IMAGE based results..
    📁 Navigate to PDF CHAT to chat with the PDF'S..
    
    Explore the Possibilities:
    
    ParvazChatBot2 is a versatile tool that can assist you in various tasks, from answering questions to analyzing images and PDF documents. Explore its capabilities and discover new ways to leverage its intelligence for your needs.
    """)

# Function to get responses from the Gemini chatbot
def get_gemini_response(question):
    try:
        response = chat.send_message(question, stream=True)
        return response
    except genai.types.generation_types.BlockedPromptException as e:
        st.error("Sorry, the provided prompt triggered a content filter. Please try again with a different prompt.")

# Function to display chat history
def display_chat_history():
    st.title("CHAT HISTORY")
    
    text_history_button, image_history_button, pdf_history_button = st.columns([1, 1, 1])

    with text_history_button:

        if st.button("Show Text Chat History", use_container_width=True):
            if 'chat_history' in st.session_state and st.session_state['chat_history']:
                st.subheader("Text Chat History:")
                for role, text in st.session_state['chat_history']:
                    if role == "YOU":
                        st.markdown(f"**{role} 👤**: {text} ")
                    elif role == "TEXT_BOT":
                        st.markdown(f"**{role} 🤖**: {text} ")
            else:
                st.error("Text Chat History is empty. Start asking questions to build the history.")

    with image_history_button:
        if st.button("Show Image Chat History", use_container_width=True):
            for history_type, header_text, emoji in [
                ('img_history', "Image Chat History:", "👤"),
                ('img_srchistory', "Image Source", "👤"),
            ]:
                history = st.session_state.get(history_type, [])
                error_message = f"{header_text} is empty. Start asking questions with images to build the history." if "Chat" in header_text else f"{header_text} is empty. Start uploading images to build the history."

                if history:
                    st.subheader(header_text)
                    for role, text in history:
                        role_prefix = emoji if role in ["YOU", "SOURCE"] else "🤖"
                        st.markdown(f"**{role} {role_prefix}**: {text}")
                else:
                    st.error(error_message)

    with pdf_history_button:
        if st.button("Show PDF Chat History", use_container_width=True):
            for history_type in ['pdf_history', 'pdf_srchistory']:
                if history := st.session_state.get(history_type):
                    title = "PDF Chat History:" if history_type == 'pdf_history' else "PDF Source History:"
                    st.subheader(title)
                    for role, user_text in history:
                        role_prefix = "👤" if role in ["YOU", "PDFS UPLOADED"] else "🤖"
                        st.markdown(f"**{role} {role_prefix}**:  {user_text} ")
                else:
                    st.error(f"{history_type.capitalize()} is empty. Start asking questions with PDFs to build the history.")

    st.warning("THE CHAT HISTORY WILL BE LOST ONCE THE SESSION EXPIRES")

# Function to chat with the Gemini chatbot
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

# Function to chat about PDF content
def chat_about_pdf(pdf_text):
    input_text = st.text_input("Ask about the PDF content")
    if input_text:
        response = get_gemini_response(input_text)
        if response:
            st.session_state['pdf_history'].append(("YOU", input_text))
            st.session_state['pdf_history'].append(("PDF_BOT", response.text))
            st.write(response.text)

# Main function to run the app
def main():
    st.set_page_config(page_title="MyAI")

    if selected == "HOME":
        st.markdown("# Welcome to My Streamlit App  ** MyAI 🦅**")
        st.markdown("#### Based on Gemini-PRO,GEMINI-PRO-Vision LLM API FROM GOOGLE")
        st.markdown("## Introduction")
        st.markdown("MyAI is an innovative chatbot application designed to provide intelligent responses to your queries. Powered by advanced language and vision models, it offers a seamless conversational experience for various use cases.")

        st.markdown("""
        ### Instructions:
        📖 Navigate to Prompt CHAT for the Text based results..
        📸 Navigate to IMAGE CHAT for the IMAGE based results..
        📁 Navigate to PDF CHAT to chat with the PDF'S..
        
        Explore the Possibilities:
        
        ParvazChatBot2 is a versatile tool that can assist you in various tasks, from answering questions to analyzing images and PDF documents. Explore its capabilities and discover new ways to leverage its intelligence for your needs.
        """)

    elif selected == "Prompt Chat":
        chat_with_gemini()

    elif selected == "CHAT HISTORY":
        display_chat_history()

    st.warning("THE CHAT HISTORY WILL BE LOST ONCE THE SESSION EXPIRES")

if __name__ == "__main__":
    main()
