import streamlit as st  # Now resolves
import os
from main import app

st.title("Friend AI - Your Empathetic Companion")

# File uploader for audio
uploaded_file = st.file_uploader("Upload audio (WAV/MP3)", type=["wav", "mp3"])

if uploaded_file:
    session_id = st.text_input(
        "Session ID (UUID)", value="123e4567-e89b-12d3-a456-426614174000"
    )
    if st.button("Chat with Friend"):
        # Call your FastAPI endpoint (or directly: transcribe_audio, etc.)
        with st.spinner("Processing..."):
            # Example: Use requests to POST to localhost:8000/chat
            import requests

            files = {"file": uploaded_file.getvalue()}
            params = {"session_id": session_id}
            response = requests.post(
                "http://localhost:8501/chat", files=files, params=params
            )
            if response.status_code == 200:
                data = response.json()
                st.write(f"Transcript: {data['transcript']}")
                st.write(f"Mood: {data['mood']}")
                st.write(f"Reply: {data['reply']}")
                st.audio(data["audio"])  # Play via URL if served
            else:
                st.error(f"Error: {response.text}")
