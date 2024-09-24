import streamlit as st
from chromadb import Client
from chromadb.config import Settings
import openai
from PyPDF2 import PdfReader
import time

# Initialize OpenAI API key
openai.api_key = st.secrets["openai_api_key"]

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file_path):
    text = ""
    with open(pdf_file_path, "rb") as file:
        pdf = PdfReader(file)
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text()
    return text

# Function to generate embeddings using OpenAI
def generate_embedding(text):
    response = openai.Embedding.create(
        model="text-embedding-ada-002",  # Use your preferred OpenAI model
        input=text
    )
    return response['data'][0]['embedding']

# Global variable for ChromaDB client
client = None

# Function to initialize the ChromaDB client with new configuration
def initialize_chroma_client():
    global client
    if client is None:
        try:
            # Initialize ChromaDB client with the new configuration settings
            client = Client(Settings(persist_directory="./chromadb_data"))
        except ValueError as e:
            st.error(f"Error: {str(e)}. Please restart the Streamlit session.")
            return None
    return client

# Function to create and initialize the ChromaDB collection

# Function to generate embeddings with retry logic
def generate_embedding_with_retry(text, retries=3, delay=20):
    for attempt in range(retries):
        try:
            response = openai.Embedding.create(
                model="text-embedding-ada-002",  # Use your preferred OpenAI model
                input=text
            )
            return response['data'][0]['embedding']
        except openai.error.RateLimitError:
            if attempt < retries - 1:
                st.warning(f"Rate limit reached. Retrying in {delay} seconds...")
                time.sleep(delay)  # Wait before retrying
            else:
                st.error("Exceeded the maximum number of retries. Please try again later.")
                return None

def create_lab4_vector_db():
    # Check if the vector DB is already in session_state
    if 'Lab4_vectorDB' not in st.session_state:
        # Initialize ChromaDB client
        client = initialize_chroma_client()
        if client is None:
            return
        
        # Check if the collection already exists
        try:
            collection = client.get_collection(name="Lab4Collection")
            st.info("Using existing collection 'Lab4Collection'.")
        except Exception:
            # Create a new collection if it doesn't exist
            collection = client.create_collection(name="Lab4Collection")
            st.success("Created new collection 'Lab4Collection'.")

        # List of PDF files to add to the collection using raw strings
        pdf_files = [
            r"C:\Users\rojab\MyData\Download\Lab4_Files\IST 644 Syllabus.pdf",
            r"C:\Users\rojab\MyData\Download\Lab4_Files\IST 652 Syllabus.pdf",
            r"C:\Users\rojab\MyData\Download\Lab4_Files\IST 652 Syllabus.pdf",
            r"C:\Users\rojab\MyData\Download\Lab4_Files\IST614 Info tech Mgmt & Policy Syllabus.pdf",
            r"C:\Users\rojab\MyData\Download\Lab4_Files\IST688-BuildingHC-AIAppsV2.pdf",
            r"C:\Users\rojab\MyData\Download\Lab4_Files\IST688-BuildingHC-AIAppsV2.pdf",
            r"C:\Users\rojab\MyData\Download\Lab4_Files\IST736-Text-Mining-Syllabus.pdf"
        ]

        # Add PDF content to the collection
        embeddings = []
        documents = []
        metadatas = []
        ids = []

        for idx, pdf_file in enumerate(pdf_files):
            text = extract_text_from_pdf(pdf_file)
            embedding = generate_embedding_with_retry(text)
            if embedding is None:
                continue  # Skip this file if we couldn't get an embedding
            embeddings.append(embedding)
            documents.append(text)
            metadatas.append({"filename": pdf_file})
            ids.append(f"doc_{idx}")  # Create a unique ID for each document

        # Add all documents, embeddings, metadata, and ids to the collection
        collection.add(embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids)

        # Store the collection in session_state
        st.session_state.Lab4_vectorDB = collection
        st.success("Vector DB initialized and stored in session state!")


# Function to test the vector database with a search query
def test_vector_db(search_query):
    if 'Lab4_vectorDB' in st.session_state:
        collection = st.session_state.Lab4_vectorDB
        # Generate embedding for the search query
        query_embedding = generate_embedding(search_query)
        # Perform search
        results = collection.query(query_embeddings=[query_embedding], n_results=3)
        # Display results
        st.write(f"Search results for '{search_query}':")
        for result in results['metadatas'][0]:
            st.write(f"- {result['filename']}")
    else:
        st.write("Lab4 vector DB is not initialized.")

# Function to handle chatbot interaction
def chatbot_interaction(user_input):
    if 'Lab4_vectorDB' in st.session_state:
        collection = st.session_state.Lab4_vectorDB
        query_embedding = generate_embedding(user_input)
        results = collection.query(query_embeddings=[query_embedding], n_results=3)
        
        # Fetch relevant data and construct prompt
        relevant_text = ""
        for result in results['documents']:
            relevant_text += result + "\n"
        
        # Construct the prompt for the chatbot
        chatbot_prompt = f"Based on the following documents, answer the query: {user_input}\n\n" + relevant_text
        
        # Send the prompt to the LLM
        response = openai.Completion.create(
            engine="text-davinci-003",  # Choose the LLM model
            prompt=chatbot_prompt,
            max_tokens=500
        )
        
        # Display chatbot response
        st.write("Chatbot Response:")
        st.write(response['choices'][0]['text'])
    else:
        st.write("Lab4 vector DB is not initialized.")

# Streamlit app layout
def lab4_page():
    st.title("Lab 4 - Vector Database with ChromaDB")

    # Button to initialize the vector DB
    if st.button("Initialize Vector DB"):
        create_lab4_vector_db()

    # Chatbot Interface
    st.subheader("Chatbot Interface")
    user_input = st.text_input("Enter your query here:")
    if st.button("Ask Chatbot"):
        chatbot_interaction(user_input)

# Main Streamlit navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Home", "Lab 4", "Chatbot"])

if page == "Lab 4":
    lab4_page()
elif page == "Chatbot":
    chatbot_interaction()
else:
    st.write("Welcome to the main page!")