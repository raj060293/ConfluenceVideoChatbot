import streamlit as st
from utils.scraper import extract_video_url
from utils.transcribe import transcribe_video_from_url
from chatbot import build_chatbot
import os
import hashlib

# === Paths ===
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "confluence_video_bot")
TRANSCRIPT_DIR = os.path.join(CACHE_DIR, "transcripts")
FAISS_DIR = os.path.join(CACHE_DIR, "faiss")
VIDEO_DIR = os.path.join(CACHE_DIR, "videos")
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

GROQ_API_KEY  = "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"

# === Streamlit UI ===
st.set_page_config(page_title="Confluence Video Q&A Bot", page_icon="🎥")
st.title("🎥 Confluence Video Q&A Chatbot")

confluence_url = st.text_input("🔗 Confluence Page URL")
api_token = st.text_input("🔐 Atlassian API Token", type="password")
email = st.text_input("📧 Atlassian Email (used with token)")

# Session state init
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "qa_chain" not in st.session_state:
    st.session_state.qa_chain = None
if "downloaded_video_path" not in st.session_state:
    st.session_state.downloaded_video_path = None

def get_cache_key_from_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()

# === Process Video ===
if st.button("🚀 Process Video") and confluence_url and api_token and email:
    cache_key = get_cache_key_from_url(confluence_url)
    video_path = os.path.join(VIDEO_DIR, f"{cache_key}.mp4")
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"{cache_key}.txt")
    faiss_cache_path = os.path.join(FAISS_DIR, f"{cache_key}")

    # Step 1: Download Video (or use cached)
    with st.spinner("Fetching video from Confluence..."):
        if not os.path.exists(video_path):
            downloaded_path = extract_video_url(confluence_url, email, api_token)
            if downloaded_path:
                os.rename(downloaded_path, video_path)
                st.success("✅ Video downloaded and cached!")
            else:
                st.error("❌ Video not found or download failed.")
                st.stop()
        else:
            st.success("✅ Using cached video.")

        st.session_state.downloaded_video_path = video_path

    # Step 2: Transcribe (if needed)
    with st.spinner("Transcribing video..."):
        if os.path.exists(transcript_path):
            with open(transcript_path, "r") as f:
                transcript = f.read()
            st.success("✅ Loaded cached transcript.")
        else:
            transcript = transcribe_video_from_url(video_path)
            with open(transcript_path, "w") as f:
                f.write(transcript)
            st.success("✅ Transcription complete and cached.")

    # Step 3: Build QA Chain (with FAISS cache path)
    with st.spinner("Building chatbot..."):
        st.session_state.qa_chain = build_chatbot(
            transcript,
            api_key=GROQ_API_KEY,
            faiss_cache_path=faiss_cache_path
        )
        st.success("✅ Chatbot is ready! Ask your questions below.")

# === Chat UI ===
if st.session_state.qa_chain:
    st.subheader("💬 Chat with the video")

    # Past chat messages
    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(message)

    # New message
    user_input = st.chat_input("Ask a question about the video...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.chat_history.append(("user", user_input))

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = st.session_state.qa_chain.invoke({
                    "question": user_input,
                    "chat_history": st.session_state.chat_history
                })
                answer = result["answer"]
                st.markdown(answer)
                st.session_state.chat_history.append(("assistant", answer))
