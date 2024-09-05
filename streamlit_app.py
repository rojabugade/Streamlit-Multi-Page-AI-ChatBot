import streamlit as st
from Lab1_upload_document import upload_document
from Lab2_ask_question import ask_question

# Function mapping to handle page navigation
PAGES = {
    "Lab 1: Upload Document": upload_document,
    "Lab 2: Ask Question": ask_question
}

# Sidebar for navigation
st.sidebar.title("Streamlit Multi-Page Chat Bot")
selected_page = st.sidebar.radio("Select a Lab", list(PAGES.keys()))

# Run the selected page function
page_function = PAGES[selected_page]
page_function()
