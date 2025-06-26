from langchain_groq import ChatGroq
from langchain.chains import ConversationalRetrievalChain
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

import os

def build_chatbot(transcript: str, api_key: str, faiss_cache_path: str):
    # 1. Prepare embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 2. Load FAISS if it exists
    if os.path.exists(faiss_cache_path):
        vectordb = FAISS.load_local(faiss_cache_path, embeddings, allow_dangerous_deserialization=True)
        print(f"✅ Loaded FAISS index from: {faiss_cache_path}")
    else:
        # Otherwise, create new FAISS index from transcript
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
        docs = [Document(page_content=chunk) for chunk in text_splitter.split_text(transcript)]

        vectordb = FAISS.from_documents(docs, embeddings)
        vectordb.save_local(faiss_cache_path)
        print(f"💾 Saved FAISS index to: {faiss_cache_path}")

    retriever = vectordb.as_retriever()

    # 3. Groq LLM
    llm = ChatGroq(groq_api_key=api_key, model_name="deepseek-r1-distill-llama-70b")

    # 4. Conversational chain
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        return_source_documents=True
    )

    return qa_chain
