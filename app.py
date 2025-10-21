import streamlit as st  # Now resolves
import os

st.title("Friend AI - Your Empathetic Companion")

# Backend API base URL
api_base_url = st.text_input("API Base URL", value="http://localhost:8000")

# File uploader for audio
uploaded_file = st.file_uploader("Upload audio (WAV/MP3)", type=["wav", "mp3"])

session_id = st.text_input(
    "Session ID (UUID)", value="123e4567-e89b-12d3-a456-426614174000"
)

if uploaded_file and st.button("Chat with Friend"):
    # Call FastAPI endpoint
    with st.spinner("Processing..."):
        import requests

        files = {
            "file": (
                getattr(uploaded_file, "name", "audio.wav"),
                uploaded_file.getvalue(),
                getattr(uploaded_file, "type", "application/octet-stream"),
            )
        }
        params = {"session_id": session_id}
        try:
            response = requests.post(f"{api_base_url}/chat", files=files, params=params)
            response.raise_for_status()
        except Exception as e:
            st.error(f"Request failed: {e}")
        else:
            data = response.json()
            st.write(f"Transcript: {data['transcript']}")
            st.write(f"Mood: {data['mood']}")
            st.write(f"Reply: {data['reply']}")

            # Play audio via FastAPI static endpoint
            audio_url = f"{api_base_url}/audio/{data['audio']}"
            st.audio(audio_url, format="audio/wav")
