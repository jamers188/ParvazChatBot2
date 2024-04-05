import streamlit as st
import os
import json
from streamlit_lottie import st_lottie
import google.generativeai as genai
from dotenv import load_dotenv
from io import BytesIO
import requests
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PIL import Image
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from google.generativeai.types import generation_types

# Load environment variables from .env file if present
load_dotenv()

API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

## function to load Gemini Pro model and get responses
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

from streamlit_option_menu import option_menu
selected = st.sidebar.selectbox("Select an Option", ["HOME", "Prompt Chat", "IMAGE CHAT", "PDF CHAT", "CHAT HISTORY"])

# Use option_menu with the defined styles
selected = option_menu(
    menu_title=None,
    options=["HOME","Prompt Chat", "IMAGE CHAT" ,"PDF CHAT","CHAT HISTORY"],
    icons=['house',"pen" ,'image','book','chat','person'],
    default_index=0,
    menu_icon='user',
    orientation="horizontal",
    styles="""
    <style>
        .option-menu {
            width: 200px; /* Set the desired width */
            margin-right: 20px; /* Set the desired spacing */
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

# Initialize streamlit app
st.set_page_config(page_title="MyAI", page_icon='🤖')

# Initialize session state for chat history, image history, PDF history, etc.
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
    # Displaying the home page content
    st.markdown("""# <span style='color:#0A2647'> Welcome to My Streamlit App  ** MyAI 🦅</span>""", unsafe_allow_html=True)
    st.markdown("""#### <span style='color:#0E6363'> Based on Gemini-PRO,GEMINI-PRO-Vision LLM API FROM GOOGLE</span>""", unsafe_allow_html=True)
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


# Function to get responses from the Gemini chatbot
def get_gemini_response(question):
    try:
        response = chat.send_message(question, stream=True)
        return response
    except generation_types.BlockedPromptException as e:
        st.error("Sorry, the provided prompt triggered a content filter. Please try again with a different prompt.")

# Displaying the chat history
if selected == 'CHAT HISTORY':
    st.title("CHAT HISTORY")
    # Create two columns for buttons
    text_history_button, image_history_button, pdf_history_button = st.columns([1, 1, 1])
    # Adjust column ratios as needed
    with text_history_button:
        # Display chat history for text if the button is clicked
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
        # Display image chat history if the button is clicked
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
        # Display pdf history for image if the button is clicked
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

# Displaying the PDF chat interface
if selected == "PDF CHAT":
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
            st.write("Extracted Text:")
            st.write(raw_text)
            response = model(raw_text)
            if response:
                st.session_state['pdf_history'].append(("PDF Uploaded", "Yes"))
                st.session_state['pdf_history'].append(("Bot", response.text))
                st.success("Response:")
                st.write(response.text)

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
                    st.write("Extracted Text:")
                    st.write(raw_text)
                    response = model(raw_text)
                    if response:
                        st.session_state['pdf_srchistory'].append(("PDF URL", pdf_url))
                        st.session_state['pdf_history'].append(("Bot", response.text))
                        st.success("Response:")
                        st.write(response.text)
                else:
                    st.error(f"Failed to retrieve PDF from URL. Status code: {response.status_code}")
            except Exception as e:
                st.error(f"Error processing PDF from URL: {str(e)}")

# Run the Streamlit app
if __name__ == "__main__":
    main()
