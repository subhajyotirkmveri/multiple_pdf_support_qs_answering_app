import streamlit as st
import timeit
import os
import base64           # to read the pdf
import yaml

from base import setup_qa_chain, run_ingest, load_config


def main():

    st.set_page_config(page_title="Chat with multiple PDFs", page_icon=":books:")
    st.title("Chat with multiple PDFs :books:")
    
    with st.sidebar:
        st.title("Settings")
        st.markdown('---')
        # Configuration File Generator
        st.title("Configuration File Generator")

        # Define options for parameters
        options = {
            "RETURN_SOURCE_DOCUMENTS": [True, False],
            "VECTOR_COUNT": [1, 2, 3],
            "CHUNK_SIZE": list(range(50, 1001)),  # Extend chunk size range from 50 to 1000
            "CHUNK_OVERLAP": list(range(0, 51)),   # Extend chunk overlap range from 0 to 50
            "DB_FAISS_PATH": "db_faiss/",
            "DATA_PATH": "data/",
            "MODEL_TYPE": ["llama", "mistral"],
            "MODEL_BIN_PATH": ['models/llama-2-7b-chat.ggmlv3.q8_0.bin', "models/Mistral-7B-Instruct-v0.1-GGUF/tree/main", "models/Mistral-7B-Instruct-v0.2-GGUF/tree/main"],
            "EMBEDDINGS": [ "sentence-transformers/all-MiniLM-L6-v2", "sentence-transformers/all-mpnet-base-v2"],
            "MAX_NEW_TOKENS": [512, 1024, 2048],
            "TEMPERATURE": [round(i * 0.01, 2) for i in range(0, 101)]  # Extend temperature range from 0.00 to 1.00
        }

        # Initialize an empty dictionary to store selected parameters
        config = {}

        # Generate UI for each parameter
        for key, value in options.items():
            if isinstance(value, list):
                config[key] = st.selectbox(f"{key}:", value)
            else:
                config[key] = st.text_input(f"{key}:", value)

        # Save the configuration to a YAML file
        if st.button("Save Configuration"):
            with open("config.yml", "w") as f:
                yaml.dump(config, f)
            st.success("Configuration saved successfully!")    
                
        # Sidebar for uploading PDF documents and running data ingestion
        st.sidebar.title("Upload PDF Documents and Run Data Ingestion")
        uploaded_files = st.sidebar.file_uploader("Upload your PDF documents here", type=['pdf'], accept_multiple_files=True)

        # Check if any files were uploaded
        if uploaded_files:
            # Loop through the uploaded files
            for uploaded_file in uploaded_files:
                cfg = load_config('config.yml')
                # Save each file to the "data" folder
                filepath = os.path.join(cfg.DATA_PATH, uploaded_file.name)
                with open(filepath, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.sidebar.success(f"{uploaded_file.name} uploaded successfully!")
            if st.button("Process"):
            # Run data ingestion
                run_ingest()
                st.sidebar.success("Process Done")
    # delete uploaded files
    if st.sidebar.button("Delete All Uploaded Files"):
        cfg = load_config('config.yml')
        folder = cfg.DATA_PATH
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

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
            
if __name__ == "__main__":
    main()

