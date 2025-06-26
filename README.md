# 🎥 Confluence Video Q&A Chatbot

A GenAI-powered Streamlit chatbot that extracts videos from Confluence pages, transcribes them using Deepgram, and answers user queries about the video content using a Retrieval-Augmented Generation (RAG) approach backed by FAISS and Groq LLM.

---

## 🚀 Features

- 🔗 Extracts videos directly from Confluence pages using Atlassian API
- 🧠 Transcribes video audio using [Deepgram API](https://deepgram.com/)
- 💬 Answers questions about the video using RAG (Retrieval-Augmented Generation)
- ⚡ Uses [FAISS](https://github.com/facebookresearch/faiss) to store transcript embeddings
- 🧵 Maintains conversational memory using LangChain's `ConversationalRetrievalChain`
- 📦 Caching system for transcripts and embeddings to avoid recomputation
- 🖥️ Streamlit-based interactive chat UI

---

## ⚙️ Setup Instructions

```bash
git clone https://github.com/raj060293/ConfluenceVideoChatbot.git
cd ConfluenceVideoChatbot

python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows

pip install -r requirements.txt

Set up API keys
Deepgram: Get your API key

Groq: Get your Groq API key

Confluence: Use Atlassian token & email (you can create API token here)

streamlit run streamlit_app.py
