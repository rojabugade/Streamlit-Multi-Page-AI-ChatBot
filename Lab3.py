import streamlit as st
import openai
def streaming_chatbot():
    st.title("💬 Talk with ChinnuTheAIBot")
    st.write("Chat with the chatbot about your queries!")

    # Set up OpenAI API key
    openai_api_key = st.secrets["openai_api_key"]

    # Initialize session state for chat history, document, and bot state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "bot_state" not in st.session_state:
        st.session_state.bot_state = "initial"  
    if "document" not in st.session_state:
        st.warning("Please upload a document first on the 'Upload Document' page.")
        return

    # Display chat history without forced font color or background color
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(
                f'<div style="text-align: right; margin: 10px 0;">'
                f'<span style="padding: 10px; display: inline-block;">'
                f'{chat["content"]}</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="text-align: left; margin: 10px 0;">'
                f'<span style="padding: 10px; display: inline-block;">'
                f'🤖 {chat["content"]}</span></div>',
                unsafe_allow_html=True,
            )

    # Create a form to handle user input and clear it after submission
    user_input = st.text_input("You:", placeholder="Type your message here...", key="input", on_change=process_input)

def process_input():
    user_input = st.session_state.input

    if user_input:
        # Append user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Check if the input is a response to "Do you want more info?"
        if st.session_state.bot_state == "waiting_for_more_info" and user_input.lower() in ["yes", "y", "no", "n"]:
            if user_input.lower() in ["yes", "y"]:
                # Provide more information and ask again in the same message
                more_info_response = get_more_info()
                combined_response = more_info_response + "\n\nDo you want more info?"
                st.session_state.chat_history.append({"role": "assistant", "content": combined_response})

            elif user_input.lower() in ["no", "n"]:
                # Ask what other question the user needs help with
                next_question_prompt = "What other question can I help you with?"
                st.session_state.chat_history.append({"role": "assistant", "content": next_question_prompt})

                # Set bot state to wait for a new question
                st.session_state.bot_state = "waiting_for_question"
        else:
            # Reset to initial state and handle the new question
            st.session_state.bot_state = "initial"
            response = get_answer_from_document(user_input, st.session_state['document'])
            combined_response = response + "\n\nDo you want more info?"
            st.session_state.chat_history.append({"role": "assistant", "content": combined_response})

            # Set bot state to wait for more info
            st.session_state.bot_state = "waiting_for_more_info"

        # Clear input field after processing
        st.session_state.input = ""

# Function to get a simple answer from the document or respond generally
def get_answer_from_document(question, document):
    lines = document.splitlines()

    # Check specific queries about the document
    if "line" in question.lower():
        line_number = extract_line_number(question)
        if line_number is not None and 0 <= line_number < len(lines):
            return f"The content on line {line_number + 1} is: {lines[line_number]}"
        else:
            return "I'm sorry, I couldn't find that line in the document. Please specify a valid line number."
    elif "document" in question.lower():
        return "This document contains important information. You can ask me about specific lines or details."
    else:
        # General handling using OpenAI for unrelated document questions
        return get_simple_answer(question)


# Helper function to extract line numbers from a question
def extract_line_number(question):
    words = question.split()
    for word in words:
        if word.isdigit():
            return int(word) - 1
    return None


# Function to get a simple answer suitable for a 10-year-old
def get_simple_answer(question):
    # Use OpenAI to generate a simple answer
    client = openai(api_key=st.secrets["openai_api_key"])
    messages = [
        {"role": "system", "content": "You are a helpful assistant that explains things simply, so a 10-year-old can understand."},
        {"role": "user", "content": question}
    ]
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=100,
        temperature=0.7
    )
    return response.choices[0].message.content


# Function to get more information
def get_more_info():
    # Generate additional details for a 10-year-old audience
    return "Here's some more information: When something is 'basefull', it might mean it's full of basics or fundamental things. It's not a common word, so it depends on how someone uses it."