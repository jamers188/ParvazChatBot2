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



# Load environment variables from .env file if present
load_dotenv()

API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)




## function to load Gemini Pro model and get responses
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

from streamlit_option_menu import option_menu
 #initialize our streamlit app
st.set_page_config(page_title="MyAI", page_icon='🤖')  # page title
#with st.sidebar:



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
if  'img_srchistory' not in  st.session_state:
        st.session_state['img_srchistory'] = []
if  'pdf_history' not in  st.session_state:
        st.session_state['pdf_history'] = []
if  'pdf_srchistory' not in  st.session_state:
        st.session_state['pdf_srchistory'] = []

 # Displaying the home page content
if selected == "HOME":
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




if selected == "Prompt Chat":
    def get_gemini_response(question):
        try:
            response = chat.send_message(question, stream=True)
            return response
        except generation_types.BlockedPromptException as e:
            st.error("Sorry, the provided prompt triggered a content filter. Please try again with a different prompt.")

    input_text = st.text_input("Ask your Question")
    
    if input_text:
        response = get_gemini_response(input_text)
        
        if response:
            st.session_state['chat_history'].append(("YOU", input_text))
            st.success("The Response is")

            # Check if response object has resolve method
            if hasattr(response, 'resolve') and callable(getattr(response, 'resolve')):
                response.resolve()
                # Handle the Gemini response format
                if hasattr(response, 'parts') and response.parts:
                    for part in response.parts:
                        # Extract text from each part
                        if hasattr(part, 'text') and part.text:
                            text_line = part.text
                            st.write(text_line)
                            st.session_state['chat_history'].append(("TEXT_BOT", text_line))
                        elif hasattr(part, 'candidates') and part.candidates:
                            # Handle candidates in the response
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
                    st.warning("Invalid response format. No parts found.")
            else:
                st.error("Error: Response object does not have a 'resolve' method.")
        else:
            st.error("Error: Failed to retrieve response from the chat service.")


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
  # Display image chat history if the button is clicked
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

        

if selected == "IMAGE CHAT":
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



if selected == "PDF CHAT":
    st.subheader("Upload PDF or Paste URL")
    upload_file = st.file_uploader("Upload PDF File", type=['pdf'])
    pdf_url = st.text_input("Paste PDF URL")

    pdf_docs = []
    if upload_file:
        pdf_docs.append(upload_file)
    elif pdf_url:
        try:
            response = requests.get(pdf_url)
            if response.status_code == 200:
                pdf_bytes = BytesIO(response.content)
                pdf_docs.append(pdf_bytes)
            else:
                st.error(f"Failed to retrieve PDF from URL. Status code: {response.status_code}")
        except Exception as e:
            st.error(f"Error loading PDF from URL: {str(e)}")

    if pdf_docs:
        # Function to extract text from PDF documents using PyMuPDF
        
        def get_pdf_text(pdf_docs):
            text = ""
            for pdf in pdf_docs:
                try:
                    if isinstance(pdf, str):  # Check if the input is a file path
                        pdf_reader = fitz.open(pdf)
                    else:
                        pdf_reader = fitz.open(stream=pdf)  # Open the PDF from BytesIO object
                    
                    # Check if the PDF contains any objects
                    if pdf_reader.page_count == 0:
                        st.error("No objects found in the PDF.")
                        continue
                    
                    for page in pdf_reader:
                        text += page.get_text()
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
            return text




        pdf_text = get_pdf_text(pdf_docs)
        st.write(pdf_text)

    def get_text_chunks(text):
     # Function to split text into smaller chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
        chunks = text_splitter.split_text(text)
        return chunks


    def get_vector_store(text_chunks):
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
            vector_store.save_local("faiss_index")
        except Exception as e:
            st.error("Enjoy")



    def get_conversational_chain():
  # Function to load and configure the conversational chain
        prompt_template = """
        Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
        provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
        Context:\n {context}?\n
        Question: \n{question}\n

        Answer:
        """

        model = ChatGoogleGenerativeAI(model="gemini-pro",temperature=0.3)

        prompt = PromptTemplate(template = prompt_template, input_variables = ["context", "question"])
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

        return chain

   

                        
              
          

    def user_input(user_question):
       # Function to process user input and generate a response
        embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
        try:
         new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
         docs = new_db.similarity_search(user_question)

         chain = get_conversational_chain()

        
         response1 = chain( {"input_documents":docs, "question": user_question} , return_only_outputs=True)


         print(response1)
         st.write("Reply: ", response1["output_text"])
         output_Text = response1["output_text"]
         st.session_state["pdf_history"].append(("YOU", user_question))
         st.session_state["pdf_history"].append(("PDF_BOT", output_Text))
        except Exception as e:
         st.error(f"An error occurred while processing the question: {str(e)}")
     #block will only execute if the script is run directly by the Python interpreter, not if it's imported as a module into another script.
# Function to fetch text from URL
# Function to get user input and chat with the chatbot
def chat_with_bot(text):
    user_input = st.text_input("Enter your message")
    if user_input:
        # Process user input and chat with the bot
        # You can replace this part with your actual chatbot logic
        st.write(f"You: {user_input}")  # Display user input
        # Here you can send the user input along with the PDF text to your chatbot and display its response
        # Example:
        response = chatbot.send_message(user_input, pdf_text=text)
        st.write(f"Bot: {response}")

# Main function
def main():
    st.title("Chat with PDF")
    st.write("Provide a URL or upload a PDF to chat about its content.")

    # Allow user to input a URL
    url = st.text_input("Enter PDF URL")
    if st.button("Chat with PDF URL"):
        if url:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    pdf_text = extract_text_from_pdf(BytesIO(response.content))
                    if pdf_text:
                        st.write("Text extracted from PDF:")
                        st.write(pdf_text)
                        # Chat with the bot using the extracted text
                        chat_with_bot(pdf_text)
                    else:
                        st.error("Failed to extract text from the PDF.")
                else:
                    st.error(f"Failed to retrieve PDF from URL. Status code: {response.status_code}")
            except Exception as e:
                st.error(f"Error processing PDF from URL: {str(e)}")

    # Allow user to upload a PDF
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    if st.button("Chat with Uploaded PDF"):
        if uploaded_file:
            # Chat with the bot using the uploaded PDF file
            pdf_text = extract_text_from_pdf(uploaded_file)
            st.write("Text extracted from PDF:")
            st.write(pdf_text)
            chat_with_bot(pdf_text)

if __name__ == "__main__":
    main()
