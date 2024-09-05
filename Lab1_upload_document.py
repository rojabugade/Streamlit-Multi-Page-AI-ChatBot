import streamlit as st
    
def upload_document():
    st.title("📄 Upload a Document to AnswerMate")
    st.write("Upload a document below that you want to ask questions about.")

    # Let the user upload a file
    uploaded_file = st.file_uploader(
        "Upload a document (.txt or .md)", type=("txt", "md")
    )

    # Store the uploaded document content in session state
    if uploaded_file:
        # Read the content of the uploaded file and store it in session state
        st.session_state['document'] = uploaded_file.read().decode()
        st.success("Document uploaded successfully!")
    else:
        st.warning("Please upload a document to proceed.")
