import streamlit as st
import requests

def _load_secrets():
    return st.secrets["GROQ_API_KEY"]

def generate_clinical_case(specialite):
    api_key = _load_secrets()
    headers = {"Authorization": f"Bearer {api_key}"}
    prompt = f"Génère un cas clinique réaliste dans la spécialité suivante : {specialite}."
    url = "https://api.groq.com/openai/v1/chat/completions"

    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
