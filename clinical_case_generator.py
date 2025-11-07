import os
import requests
import time
import json
import streamlit as st
from typing import Optional


def _load_secrets():
    """Charge la clé API Groq et le modèle depuis .streamlit/secrets.toml"""
    try:
        groq_api_key = st.secrets.get("GROQ_API_KEY")
        model = st.secrets.get("MODEL", "llama-3.3-70b-versatile")
        return groq_api_key, model
    except Exception:
        return None, "llama-3.3-70b-versatile"


def generate_clinical_case(model_name: str, specialty: str, severity: str, groq_api_key: Optional[str] = None) -> str:
    """Génère un cas clinique en fonction de la spécialité et de la gravité."""
    if not groq_api_key:
        groq_api_key, _ = _load_secrets()
    if not groq_api_key:
        raise RuntimeError("⚠️ Clé API Groq manquante dans .streamlit/secrets.toml")

    prompt = f"""
Tu es un expert en formation clinique pour étudiants infirmiers.

Génère un cas clinique complet et réaliste dans la spécialité suivante : **{specialty}**.
Le cas doit être de gravité **{severity}**.

Structure attendue (sans mentionner les titres dans le texte final) :
- Présentation du patient
- Contexte d’hospitalisation
- Histoire de la maladie ou situation actuelle
- Observation clinique (sans chiffres)
- Examens complémentaires éventuels

Le ton doit être professionnel, pédagogique et réaliste.  
N'inclus **aucune solution ni interprétation**.  
N’ajoute pas de titres ou de sections explicites dans le texte.
"""

    api_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "Tu es un expert en soins infirmiers et formation clinique."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 800,
    }

    for attempt in range(3):
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            try:
                return response.json()["choices"][0]["message"]["content"].strip()
            except Exception:
                return json.dumps(response.json(), ensure_ascii=False)
        elif response.status_code in (429, 503):
            time.sleep(2 ** attempt)
            continue
        else:
            raise RuntimeError(f"Groq API error {response.status_code}: {response.text}")

    raise RuntimeError("❌ Échec de la génération après plusieurs tentatives.")
