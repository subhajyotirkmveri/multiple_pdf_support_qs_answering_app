import streamlit as st
import timeit
import os

from base import setup_qa_chain, run_ingest


def main():

    st.set_page_config(page_title="Chat with multiple PDFs", page_icon=":books:")
    st.title("Chat with multiple PDFs :books:")
    
    with st.sidebar:
        st.title("Settings")
        st.markdown('---')
        
        # Sidebar for uploading PDF documents and running data ingestion
        st.sidebar.title("Upload PDF Documents and Run Data Ingestion")
        uploaded_files = st.sidebar.file_uploader("Upload your PDF documents here", type=['pdf'], accept_multiple_files=True)

        # Check if any files were uploaded
        if uploaded_files:
            # Loop through the uploaded files
            for uploaded_file in uploaded_files:
                # Save each file to the "data" folder
                filepath = os.path.join("data", uploaded_file.name)
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.sidebar.success(f"{uploaded_file.name} uploaded successfully!")
            if st.button("Process"):
            # Run data ingestion
                run_ingest()
                st.sidebar.success("Process Done")


    # Previous messages display
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"**User:** {message['content']}")
        elif message["role"] == "assistant":
            st.markdown(f"**Assistant:** {message['content']}")

    # Text input for user query
    query = st.text_input("Ask the Question", placeholder="Type your question here...")

    # Submit button for user query
    if st.button("Submit"):
        if query:
            start_time = timeit.default_timer()
            # Run QA chain to get the response
            qa_chain = setup_qa_chain()
            response = qa_chain({'query': query})

            # Display the result
            st.write(f'\nAnswer: {response["result"]}')
            st.write('=' * 50)
            end_time = timeit.default_timer()
            #st.write(f"Time to retrieve answer: {end_time - start_time}")
            st.write("Time to retrieve answer:", end_time - start_time, "sec")
            # Add user query and assistant response to session state
            st.session_state.messages.append({"role": "user", "content": query})
            st.session_state.messages.append({"role": "assistant", "content": response["result"]})
            
            # Option to delete all uploaded files after chat
            if st.button("Delete Uploaded Files"):
                folder = 'data'
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        st.error(f"Error: {e}")


if __name__ == "__main__":
    main()

