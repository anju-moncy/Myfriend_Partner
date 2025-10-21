import streamlit as st  # Now resolves
import os
import requests

st.title("Friend AI - Your Empathetic Companion")

# File uploader for audio
uploaded_file = st.file_uploader("Upload audio (WAV/MP3)", type=["wav", "mp3"])

if uploaded_file:
    session_id = st.text_input(
        "Session ID (UUID)", value="123e4567-e89b-12d3-a456-426614174000"
    )
    if st.button("Chat with Friend"):
        with st.spinner("Processing..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            params = {"session_id": session_id}
            # FastAPI usually runs on 8000
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            response = requests.post(f"{api_base}/chat", files=files, params=params)
            if response.status_code == 200:
                data = response.json()
                st.write(f"Transcript: {data['transcript']}")
                st.write(f"Mood: {data['mood']}")
                st.write(f"Reply: {data['reply']}")
                audio_url = f"{api_base}/audio/{data['audio']}"
                st.audio(audio_url)
            else:
                try:
                    st.error(f"Error: {response.status_code} - {response.json()}")
                except Exception:
                    st.error(f"Error: {response.status_code} - {response.text}")
