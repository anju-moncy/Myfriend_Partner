import streamlit as st
import requests

st.set_page_config(page_title="Friend AI - Your Empathetic Companion")
st.title("Friend AI - Your Empathetic Companion")

# Backend base URL
API_BASE = st.secrets.get("API_BASE", "http://localhost:8000")

uploaded_file = st.file_uploader("Upload audio (WAV/MP3)", type=["wav", "mp3"])
session_id = st.text_input(
    "Session ID (UUID)", value="123e4567-e89b-12d3-a456-426614174000"
)

if st.button("Chat with Friend"):
    if not uploaded_file:
        st.warning("Please upload an audio file first.")
    else:
        with st.spinner("Processing..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            params = {"session_id": session_id}
            try:
                response = requests.post(f"{API_BASE}/chat", files=files, params=params)
            except Exception as ex:
                st.error(f"Failed to reach backend: {ex}")
            else:
                if response.status_code == 200:
                    data = response.json()
                    st.write(f"Transcript: {data['transcript']}")
                    st.write(f"Mood: {data['mood']}")
                    st.write(f"Reply: {data['reply']}")
                    audio_url = f"{API_BASE}/audio/{data['audio']}"
                    st.audio(audio_url, format="audio/wav")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
