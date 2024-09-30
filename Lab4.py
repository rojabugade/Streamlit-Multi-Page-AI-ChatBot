import os
import time
import PyPDF2
import streamlit as st
import openai
__import__('pysqlite3') 
import sys 
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb
from chromadb.utils import embedding_functions
import tiktoken
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Initialize OpenAI API key
openai.api_key = st.secrets["openai_api_key"]

# Initialize ChromaDB client with persistent storage
def initialize_chromadb():
    if "Lab4_vectorDB" not in st.session_state:
        client = chromadb.PersistentClient(path="./chroma_db")
        st.session_state.Lab4_vectorDB = client.get_or_create_collection(
            name="Lab4Collection"
        )
        st.success("ChromaDB collection loaded successfully!")

        # Debugging: Print the collection to ensure it's initialized
        st.write("Loaded collection: ", st.session_state.Lab4_vectorDB)

        # Check if there are any documents stored in the collection
        num_docs = st.session_state.Lab4_vectorDB.count()
        st.write(f"Number of documents in the collection: {num_docs}")


# Function to count tokens using tiktoken
def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(string))


# Function to get embeddings for the query using text-embedding-ada-002
def get_embedding(text):
    response = openai.Embedding.create(
        model="text-embedding-ada-002", input=text  # Using ada for embedding
    )
    return np.array(response["data"][0]["embedding"])


# Function to extract text from a PDF and split it into chunks using PyPDF2
def extract_text_chunks_from_pdfs(folder_path, chunk_size=1000):
    pdf_chunks = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            text = ""
            with open(file_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                # Extract text from all pages in the PDF
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text()
            # Split text into chunks
            chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
            pdf_chunks[filename] = chunks
    return pdf_chunks


# Function to get embeddings for a list of text chunks with rate limit handling
def get_embeddings_for_chunks(chunks):
    embeddings = []
    for chunk in chunks:
        try:
            response = openai.Embedding.create(
                input=chunk, model="text-embedding-ada-002"  # Cheaper embedding model
            )
            embeddings.append(response["data"][0]["embedding"])
            time.sleep(
                1
            )  # Add a 1-second delay between each request to avoid rate limiting
        except openai.RateLimitError as e:
            st.error(
                f"Rate limit hit: {str(e)}. Waiting for 10 seconds before retrying..."
            )
            time.sleep(10)  # If rate limit is hit, wait 10 seconds and retry
            return get_embeddings_for_chunks(chunks)  # Retry the function
    return embeddings


# Function to query the vector database and get relevant context
def get_relevant_context(query, max_tokens=6000):
    if "Lab4_vectorDB" in st.session_state:
        # Generate the embedding for the user's query
        query_embedding = openai.Embedding.create(
            input=query, model="text-embedding-ada-002"
        )["data"][0]["embedding"]

        # Search the ChromaDB collection for the most relevant documents based on the query embedding
        results = st.session_state.Lab4_vectorDB.query(
            query_embeddings=[query_embedding],
            n_results=5,  # Adjust based on how many results you want
            include=["documents", "metadatas"],
        )

        # Combine results into a readable context
        context = ""
        for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
            new_context = f"From document '{metadata['filename']}':\n{doc}\n\n"
            if (
                num_tokens_from_string(context + new_context, "cl100k_base")
                <= max_tokens
            ):
                context += new_context
            else:
                break
        return context
    return ""


# Function to generate a response based on the user's question
def generate_response(query):
    context = get_relevant_context(query)
    if context:
        # Ask GPT to provide an answer using the relevant context from the database
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"},
            ],
            max_tokens=300,
        )
        return response["choices"][0]["message"]["content"]
    else:
        return "I couldn't find relevant information in the documents."


# Add the chatbot UI in your Streamlit app
def chatbot_page():
    st.title("Course Information Chatbot")

    # User input to ask questions
    query = st.text_input("Ask a question about the course:")

    if query and st.button("Submit"):
        # Generate the response from the chatbot
        response = generate_response(query)

        # Display the chatbot's response
        st.write("### ChinnuTheAIBot")
        st.write(response)


# Index PDFs into ChromaDB only if they haven't been indexed yet
def index_pdfs_in_chromadb():
    if "Lab4_vectorDB" in st.session_state:
        # Check if the collection is already populated
        if (
            st.session_state.Lab4_vectorDB.count() == 0
            and "indexed" not in st.session_state
        ):
            st.write("No documents found in ChromaDB. Indexing PDFs now...")
            pdf_chunks = extract_text_chunks_from_pdfs("All_pdf_files")

            # Loop through PDFs and their chunks
            for filename, chunks in pdf_chunks.items():
                st.write(f"Indexing {filename}...")
                embeddings = get_embeddings_for_chunks(chunks)
                # Add each chunk and its embedding to ChromaDB
                for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk_id = (
                        f"{filename}chunk{idx}"  # Create a unique ID for each chunk
                    )
                    st.session_state.Lab4_vectorDB.add(
                        ids=[chunk_id],  # Unique ID
                        documents=[chunk],
                        embeddings=[embedding],
                        metadatas=[{"filename": filename}],
                    )
            st.session_state.indexed = (
                True  # Set a flag to indicate indexing is complete
            )
            st.success("All PDFs indexed successfully!")
        else:
            st.write("Documents are already indexed, skipping re-indexing.")


# Call this function in the main app logic to prevent re-indexing
def lab4_page():
    # Initialize the ChromaDB collection automatically
    initialize_chromadb()

    # Perform indexing only if not already done
    index_pdfs_in_chromadb()

    # Display the number of documents after indexing
    st.write(
        f"Number of documents after indexing: {st.session_state.Lab4_vectorDB.count()}"
    )
    chatbot_page()