import chromadb
import streamlit as st
from chromadb import Client
from chromadb.config import Settings
import openai
from PyPDF2 import PdfReader
import time
import numpy as np

# Check SQLite version compatibility
import sqlite3
sqlite_version = sqlite3.sqlite_version
if sqlite_version < "3.35.0":
    st.warning(f"Warning: Your SQLite version is {sqlite_version}. Some ChromaDB features may not work.")

print("ChromaDB version:", chromadb.__version__)
print("NumPy version:", np.__version__)
print("SQLite version:", sqlite_version)

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
    try:
        response = openai.Embedding.create(
            model="text-embedding-ada-002",  # Use your preferred OpenAI model
            input=text
        )
        import pdb
        pdb.set_trace()
        return response['data'][0]['embedding']
    except Exception as e:
        st.error(f"Error generating embedding: {e}")
        return None

# Global variable for ChromaDB client
client = None

# Function to initialize the ChromaDB client with new configuration
def initialize_chroma_client():
    global client
    if client is None:
        try:
            # Simplified configuration without advanced settings
            client = Client(Settings())
        except Exception as e:
            st.error(f"Error: {str(e)}. Please restart the Streamlit session.")
            return None
    return client

# Function to generate embeddings with retry logic
def generate_embedding_with_retry(text, retries=3, delay=20):
    for attempt in range(retries):
        embedding = generate_embedding(text)
        import pdb
        pdb.set_trace()
        if embedding:
            return embedding
        if attempt < retries - 1:
            st.warning(f"Rate limit or error encountered. Retrying in {delay} seconds...")
            time.sleep(delay)
    st.error("Exceeded the maximum number of retries. Please try again later.")
    return None

# Function to create and initialize the ChromaDB collection
def create_lab4_vector_db():
    if 'Lab4_vectorDB' not in st.session_state:
        # Initialize ChromaDB client
        client = initialize_chroma_client()
        if client is None:
            return

        try:
            # Check if the collection already exists
            collection = client.get_collection(name="Lab4Collection")
            st.info("Using existing collection 'Lab4Collection'.")
        except Exception:
            # Create a new collection if it doesn't exist
            collection = client.create_collection(name="Lab4Collection")
            st.success("Created new collection 'Lab4Collection'.")

        # List of PDF files to add to the collection
        pdf_files = ["All_pdf_files/IST 644 Syllabus.pdf",
                     "All_pdf_files/IST 652 Syllabus.pdf",
                     "All_pdf_files/IST 652 Syllabus.pdf",
                     "All_pdf_files/IST614 Info tech Mgmt & Policy Syllabus.pdf",
                     "All_pdf_files/IST688-BuildingHC-AIAppsV2.pdf",
                     "All_pdf_files/IST688-BuildingHC-AIAppsV2.pdf",
                     "All_pdf_files/IST736-Text-Mining-Syllabus.pdf"]
    

        embeddings = []
        documents = []
        metadatas = []
        ids = []

        for idx, pdf_file in enumerate(pdf_files):
            text = extract_text_from_pdf(pdf_file)
            embedding = generate_embedding_with_retry(text)
            import pdb
            pdb.set_trace()
            if embedding is None:
                continue  # Skip this file if we couldn't get an embedding
            embeddings.append(embedding)
            documents.append(text)
            metadatas.append({"filename": pdf_file})
            ids.append(f"doc_{idx}")

        if len(embeddings) == len(documents) == len(ids):
            st.info(f"Prepared {len(ids)} embeddings and documents.")
        else:
            st.error("Mismatch between the number of embeddings, documents, and IDs.")

        try:
            # Add all documents, embeddings, metadata, and ids to the collection
            collection.add(embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids)
            st.success("Documents added to the collection successfully.")
        except Exception as e:
            st.error(f"Failed to add documents to collection: {e}")

        # Store the collection in session_state
        st.session_state.Lab4_vectorDB = collection
        st.success("Vector DB initialized and stored in session state!")
    else:
        st.success("Lab4 vector DB already initialized.")

# Function to handle chatbot interaction
def chatbot_interaction(user_input):
    if 'Lab4_vectorDB' in st.session_state:
        collection = st.session_state.Lab4_vectorDB
        query_embedding = generate_embedding_with_retry(user_input)
        import pdb
        pdb.set_trace()
        if query_embedding is None:
            st.error("Failed to generate query embedding.")
            return
        try:
            import pdb
            pdb.set_trace()
            results = collection.query(query_embeddings=[query_embedding], n_results=3)
            st.write("Query results:", results)
        except Exception as e:
            st.error(f"Error in querying collection: {e}")
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
else:
    st.write("Welcome to the main page!")
