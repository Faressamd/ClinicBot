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
    """Génère un cas clinique en français à l'aide de l'API Groq"""
    if not groq_api_key:
        groq_api_key, _ = _load_secrets()
    if not groq_api_key:
        raise RuntimeError("⚠️ Clé API Groq manquante dans .streamlit/secrets.toml")

    if not model_name:
        _, model_name = _load_secrets()

    prompt = """
Génère un cas clinique complet et structuré destiné à un étudiant infirmier, y compris pour les nouveaux reçus.
Ne donne aucune solution ni interprétation.

Le cas doit suivre la logique suivante :
- Présentation du patient
- Contexte d’hospitalisation
- Histoire de la maladie / Situation actuelle
- Observation / Données cliniques
- Examens complémentaires

Cependant, **n’indique pas ces titres dans le texte final**.  
Écris le cas sous forme d’un récit fluide et cohérent, au style professionnel, clair et clinique.  
N’inclus pas les signes vitaux, les données d’observation chiffrées ni les résultats du dossier.
"""



    api_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "Tu es un expert en soins infirmiers et formation clinique."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 700,
    }

    for attempt in range(3):
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()
            try:
                return data["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError):
                return json.dumps(data, ensure_ascii=False)

        elif response.status_code in (429, 503):
            time.sleep(2 ** attempt)
            continue
        else:
            raise RuntimeError(f"Groq API error {response.status_code}: {response.text}")

    raise RuntimeError("❌ Échec de la génération après plusieurs tentatives.")
