import streamlit as st
import openai
import time

# Define the bot icon URL - Replace with your bot's actual icon URL
BOT_ICON_URL = "HWs\Bot Icon.gif"  # Replace with the correct URL of your desired bot icon image

def streaming_chatbot():
    st.title("Talk with ChinnuTheAIBot")
    st.write("Chat with the chatbot about your queries!")

    # Sidebar Inputs
    st.sidebar.title("Configuration")
    url1 = st.sidebar.text_input("Enter the first URL:")
    url2 = st.sidebar.text_input("Enter the second URL:")

    # Model Selection
    llm_model = st.sidebar.selectbox("Choose LLM model:", ["OpenAI GPT-3.5", "OpenAI GPT-4", "Vendor1 Model", "Vendor2 Model"])

    # Memory Type Selection
    memory_type = st.sidebar.selectbox(
        "Select Memory Type:",
        ["Buffer of 5 questions", "Conversation summary", "Buffer of 5,000 tokens"]
    )

    # Initialize session state for chat history if not already set
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Initialize session state to control input reset
    if "input_reset" not in st.session_state:
        st.session_state.input_reset = False

    # CSS for sticky input box and overall layout adjustments
    st.markdown(
        """
        <style>
        .chat-container {
            max-height: 75vh;
            overflow-y: auto;
            padding-bottom: 60px; /* Space for the input */
        }
        .input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #ffffff;
            padding: 10px 20px;
            border-top: 1px solid #ddd;
            display: flex;
            align-items: center;
            z-index: 1000;
        }
        .input-field {
            flex-grow: 1;
            margin-right: 10px;
        }
        button {
            background-color: #ff4b4b;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #ff3333;
        }
        </style>
        """, 
        unsafe_allow_html=True
    )

    # Display chat history in a scrollable container with fixed height
    chat_container = st.empty()  # Use empty to dynamically update chat
    with chat_container.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        display_chat_history()
        st.markdown('</div>', unsafe_allow_html=True)

    # Sticky input at the bottom of the page
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    # Reset input field using session state flag
    if st.session_state.input_reset:
        user_input = st.text_input("", placeholder="Type your message here...", key="input_text", label_visibility="collapsed", value="")
        st.session_state.input_reset = False
    else:
        user_input = st.text_input("", placeholder="Type your message here...", key="input_text", label_visibility="collapsed")
    
    submit_button = st.button("Send", key="send_button")
    st.markdown('</div>', unsafe_allow_html=True)

    # Check for user input without modifying session state directly
    if submit_button and user_input:
        # Add user query to chat history
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Fetch answers using the selected LLM model and memory type
        answer = get_response_from_llm(user_input, url1, url2, llm_model, memory_type)

        # Add the assistant's response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": answer})

        # Set the flag to reset the input field
        st.session_state.input_reset = True

def display_chat_history():
    """Function to display chat history from session state."""
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            # Display user messages on the right
            st.markdown(
                f"""
                <div style='text-align: right; margin: 10px 0;'>
                    <span style='display: inline-block;'>
                        {chat['content']}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Display bot messages on the left with bot icon
            st.markdown(
                f"""
                <div style='text-align: left; margin: 10px 0; display: flex; align-items: center;'>
                    <span style='display: inline-block;'>
                        🤖 {chat['content']}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )

def get_response_from_llm(question, url1, url2, model, memory):
    # Simulate fetching content from the URLs (actual implementation may involve web scraping or API requests)
    content1 = fetch_content(url1)
    content2 = fetch_content(url2)

    # Combine documents and handle according to the selected memory type
    combined_content = (content1 + "\n\n" + content2) if content1 and content2 else content1 or content2

    # Call the appropriate model based on the user selection
    if model == "OpenAI GPT-3.5":
        response = openai_response(question, combined_content, "gpt-3.5-turbo")
    elif model == "OpenAI GPT-4":
        response = openai_response(question, combined_content, "gpt-4")
    else:
        response = other_llm_response(question, combined_content, model)

    return response

def openai_response(question, content, model):
    openai.api_key = st.secrets["openai_api_key"]
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Content: {content}\n\nQuestion: {question}"}
    ]
    
    # Retry mechanism with a maximum number of retries
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            # Create an empty container to update with the streamed response
            response_container = st.empty()
            full_response = ""

            # Generate the response with streaming enabled
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                stream=True  # Enable streaming
            )

            # Stream the response in real-time
            for chunk in response:
                if 'choices' in chunk and len(chunk['choices']) > 0:
                    message_chunk = chunk['choices'][0]['delta'].get('content', '')
                    full_response += message_chunk
                    response_container.markdown(full_response)  # Update the container with the new content

            return full_response

        except openai.error.RateLimitError as e:
            st.warning(f"Rate limit reached. Retrying in 20 seconds... (Attempt {retries + 1} of {max_retries})")
            retries += 1
            time.sleep(20)  # Wait for 20 seconds before retrying

    # Return a message if retries are exhausted
    return "Sorry, the request could not be completed due to rate limits. Please try again later."

def other_llm_response(question, content, model):
    # Placeholder function for other LLM vendors
    return f"Response from {model} not implemented."

def fetch_content(url):
    # Placeholder function to simulate fetching content from URLs
    # You would replace this with actual web scraping or API fetching logic
    return f"Fetched content from {url}"
