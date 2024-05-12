import streamlit as st
import os
import timeit
from langchain.llms import CTransformers
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.llms import CTransformers
import box
import yaml

import os

def load_config(config_file_path):
    with open(config_file_path, 'r', encoding='utf8') as ymlfile:
        cfg = box.Box(yaml.safe_load(ymlfile))
    return cfg


def run_ingest():
    cfg = load_config('config.yml')
    
    if not os.path.exists(cfg.DATA_PATH):
        os.makedirs(cfg.DATA_PATH)
        print("Data Folder created successfully")
    else:
        print("Data Folder already exists")  
          
    if not os.path.exists(cfg.DB_FAISS_PATH):
        os.makedirs(cfg.DB_FAISS_PATH)
        print("DB Fiass Folder created successfully")
    else:
        print("DB Faiss Folder already exists")
        
    loader = DirectoryLoader(cfg.DATA_PATH,
                             glob='*.pdf',
                             loader_cls=PyPDFLoader)

    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=cfg.CHUNK_SIZE,
                                                   chunk_overlap=cfg.CHUNK_OVERLAP)
    texts = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name=cfg.EMBEDDINGS,
                                       model_kwargs={'device': 'cpu'})

    vectorstore = FAISS.from_documents(texts, embeddings)
    vectorstore.save_local(cfg.DB_FAISS_PATH)

def setup_llm():
    cfg = load_config('config.yml')
    llm = CTransformers(model=cfg.MODEL_BIN_PATH,
                        model_type=cfg.MODEL_TYPE
    )

    return llm


# Define the prompt template
prompt_template = """Use the following pieces of information to answer the user's question.
    Try to provide as much text as possible from "response". If you don't know the answer, please just say 
    "I don't know the answer". Don't try to make up an answer.
    
    Context: {context},
    Question: {question}
    
    Only return correct and helpful answer below and nothing else.
    Helpful answer:
"""

def set_qa_prompt():
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return prompt
    


def build_retrieval_qa_chain(llm, prompt):
    cfg = load_config('config.yml')
    embeddings = HuggingFaceEmbeddings(model_name=cfg.EMBEDDINGS,
                                       model_kwargs={'device': 'cpu'})
    vectordb = FAISS.load_local(cfg.DB_FAISS_PATH, embeddings)
    retriever = vectordb.as_retriever(search_kwargs={'k': cfg.VECTOR_COUNT})

    qa_chain = RetrievalQA.from_chain_type(llm=llm,
                                           chain_type='stuff',
                                           retriever=retriever,
                                           input_key="query",
                                           return_source_documents=cfg.RETURN_SOURCE_DOCUMENTS,
                                           chain_type_kwargs={'prompt': prompt})
    return qa_chain

def setup_qa_chain():
    llm = setup_llm()
    qa_prompt = set_qa_prompt()
    qa_chain = build_retrieval_qa_chain(llm, qa_prompt)

    return qa_chain

