import streamlit as st
import openai

def ask_question():
    st.title("❓ Ask a Question AnswerMate")
    st.write("Ask a question about the uploaded document.")

    # Ask user for their OpenAI API key
    openai_api_key = st.secrets["openai_api_key"]

    # Check if a document has been uploaded
    document = st.session_state.get('document', None)
    if not document:
        st.warning("Please upload a document first on the 'Upload Document' page.")
        return

    # Ask the user for a question
    question = st.text_area(
        "Now ask a question about the document!",
        placeholder="Can you give me a short summary?",
    )

    if question:
        # Create an OpenAI client
        client = openai(api_key=openai_api_key)
        
        # Prepare the messages for the OpenAI API
        messages = [
            {
                "role": "user",
                "content": f"Here's a document: {document} {question}",
            }
        ]

        # Generate an answer using the OpenAI API
        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
            )
            st.write_stream(stream)
        except Exception as e:
            st.error(f"An error occurred: {e}")
