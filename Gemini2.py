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

# Initialize session state for chat history, image history, pdf history if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'img_history' not in st.session_state:
    st.session_state['img_history'] = []
if  'img_srchistory' not in  st.session_state:
    st.session_state['img_srchistory'] = []
if  'pdf_history' not in  st.session_state:
    st.session_state['pdf_history'] = []
if  'pdf_srchistory' not in  st.session_state:
    st.session_state['pdf_srchistory'] = []

# Displaying the home page content
with st.sidebar:
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

# Function to get responses from the Gemini chatbot
def get_gemini_response(question):
    try:
        response = chat.send_message(question, stream=True)
        return response
    except generation_types.BlockedPromptException as e:
        st.error("Sorry, the provided prompt triggered a content filter. Please try again with a different prompt.")

# Function to extract text from PDF documents
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            # Check file size before reading
            if pdf.size > 200 * 1024 * 1024:  # 200 MB in bytes
                st.warning(f"Skipping file: {pdf.name}. File size exceeds 200 MB.")
                continue
                
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
        except Exception as e:
            if type(e).__name__ == "PdfReadError":
                st.warning(f"Skipping non-PDF file: {pdf.name}. Error: {str(e)}")
                continue
            else:
                raise  # Raise the exception if it's not a PdfReadError
    return text

# Function to split text into smaller chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

# Function to load and configure the conversational chain
def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

# Main function for PDF chat functionality
def main_pdf_chat():
    st.header("Chat with PDF ")
    user_question = st.chat_input("Ask a Question from the PDF Files")
    if user_question:
        user_input(user_question)

    st.title("Menu:")
    option = st.radio("Choose an option", ["Upload PDF", "Provide PDF URL"])
    
    if option == "Upload PDF":
        pdf_docs = st.file_uploader("Upload your PDF Files and Click on the Submit & Process Button", accept_multiple_files=True)
    elif option == "Provide PDF URL":
        pdf_url = st.text_input("Paste PDF URL Here:")
        if pdf_url:
            try:
                response = requests.get(pdf_url)
                if response.status_code == 200:
                    pdf_docs = [BytesIO(response.content)]
                else:
                    st.error(f"Failed to retrieve PDF from URL. Status code: {response.status_code}")
            except Exception as e:
                st.error(f"Error loading PDF from URL: {str(e)}")
    
    if st.button("Submit & Process"):
        with st.spinner("Processing..."):
            if 'pdf_docs' not in locals():
                st.error("Please upload PDF files or provide PDF URL.")
                return
            
            pdf_docs = [pdf for pdf in pdf_docs if pdf.name.endswith('.pdf')]
            if not pdf_docs:
                st.error("Please upload PDF files only.")
                return

            raw_text = get_pdf_text(pdf_docs)
            text_chunks = get_text_chunks(raw_text)
            get_vector_store(text_chunks)
            st.success("Done")
            pdf_names = [pdf.name for pdf in pdf_docs]
            st.session_state["pdf_srchistory"].append(("PDFS UPLOADED", pdf_names))
            st.balloons()

# Function to process user input and generate a response
def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    try:
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)
        chain = get_conversational_chain()
        response1 = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        st.write("Reply: ", response1["output_text"])
        output_Text = response1["output_text"]
        
        # Check if the entry already exists in pdf_history
        if ("YOU", user_question) not in st.session_state["pdf_history"]:
            st.session_state["pdf_history"].append(("YOU", user_question))
        if ("PDF_BOT", output_Text) not in st.session_state["pdf_history"]:
            st.session_state["pdf_history"].append(("PDF_BOT", output_Text))
    except Exception as e:
        st.error(f"An error occurred while processing the question: {str(e)}")

# Main function
def main():
    if selected == "Prompt Chat":
        input_text = st.text_input("Ask your Question")
        if input_text:
            response = get_gemini_response(input_text)
            if response:
                st.session_state['chat_history'].append(("YOU", input_text))
                st.success("The Response is")
                if hasattr(response, 'resolve') and callable(getattr(response, 'resolve')):
                    response.resolve()
                    if hasattr(response, 'parts') and response.parts:
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
                    st.error("Error: Response object does not have a 'resolve' method.")
            else:
                st.error("Error: Failed to retrieve response from the chat service.")

elif selected == "IMAGE CHAT":
    vision_model = genai.GenerativeModel('gemini-pro-vision')
    
    def vscontent(input_text_1, image):
        response = vision_model.generate_content([input_text_1, image], stream=True)
        return response
    
    

    # Option to choose between file upload and URL input

    option = st.radio("Choose an option", ["Upload Image", "Provide Image URL"])

    if option == "Upload Image":
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            try:
                image = Image.open(uploaded_file)
                st.image(image, caption='Uploaded Image', use_column_width=True)
                st.session_state['img_srchistory'].append(("SOURCE", option))
            except Exception as e:
              st.error(f"Error loading uploaded image: {str(e)}")


    elif option == "Provide Image URL":
         image_url = st.text_input("Paste Image URL Here(Paste Image address):")
         if image_url:
             try:
                 response = requests.get(image_url)
                 if response.status_code == 200:
                     image = Image.open(BytesIO(response.content))
                     st.image(image, caption='Image from URL', use_column_width=True)
                     st.session_state['img_srchistory'].append(("SOURCE", option))
                 else:
                     st.error(f"Failed to retrieve image from URL. Status code: {response.status_code}")
             except Exception as e:
                 st.error(f"Error loading image from URL: {str(e)}")




                

    
    # Use the vision model
    if 'image' in locals():
        try:
            input_text_1 = st.chat_input("Ask about the image")
            if input_text_1:
                response = vscontent(input_text_1, image)
                response.resolve()

                st.session_state['img_history'].append(("YOU", input_text_1))
                st.session_state['img_history'].append(("IMAGE_BOT", response.text))
                st.balloons()
                st.markdown(f"**Generated text:** {response.text}")

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

    elif selected == "PDF CHAT":
        main_pdf_chat()

    elif selected == 'CHAT HISTORY':
        st.title("CHAT HISTORY")
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

if __name__ == "__main__":
    main()
