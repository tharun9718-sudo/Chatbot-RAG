"""
Simple Streamlit UI for RAG Chatbot
"""
import streamlit as st
import requests
import os

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Jenny - RAG Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Jenny - Your AI Assistant")

with st.sidebar:
    st.header("🚑 ABCD GENERAL HOSPITAL CHATBOT")
    
    st.subheader("Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'txt', 'docx', 'doc'],
        help="Upload PDF, TXT, or DOCX files"
    )
    
    if uploaded_file and st.button("Upload"):
        with st.spinner("Uploading..."):
            files = {'file': uploaded_file}
            response = requests.post(f"{API_URL}/upload_document", files=files)
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ {result['message']}")
            else:
                st.error("❌ Upload failed")
    
    st.divider()
    
    st.subheader("Add URL")
    url_input = st.text_input("Enter website URL")
    
    if url_input and st.button("Add URL"):
        with st.spinner("Ingesting URL..."):
            response = requests.post(
                f"{API_URL}/ingest_url",
                json={"url": url_input}
            )
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ {result['message']}")
            else:
                st.error("❌ Failed to ingest URL")
    
    st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm Jenny, your AI assistant. 😊 Upload some documents/URLs and ask me anything!"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        if "sources" in message and message["sources"]:
            with st.expander("📄 View Sources"):
                for i, source in enumerate(message["sources"], 1):
                    st.text(f"Source {i}:")
                    st.caption(source['content'])
                    st.json(source['metadata'])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = requests.post(
                f"{API_URL}/ask_question",
                json={"question": prompt, "k": 4}
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('answer', 'Sorry, I encountered an error.')
                sources = result.get('sources', [])
                
                st.markdown(answer)
                
                if sources:
                    with st.expander("📄 View Sources"):
                        for i, source in enumerate(sources, 1):
                            st.text(f"Source {i}:")
                            st.caption(source['content'])
                            st.json(source['metadata'])
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
            else:
                error_msg = "Sorry, I couldn't process your question. Please try again."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })