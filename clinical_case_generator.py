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

    prompt = f"""
Tu es un formateur clinique expérimenté pour étudiants en soins infirmiers.

Ta mission est de générer un cas clinique réaliste en FRANÇAIS pour la spécialité suivante : {specialty}.
Niveau de gravité : {severity}.

OBJECTIF PÉDAGOGIQUE :
Ce cas doit obliger l’étudiant à analyser, réfléchir et proposer lui-même le diagnostic et la prise en charge.

IMPORTANT (RÈGLE ABSOLUE) :
Tu ne dois PAS donner :
- le diagnostic final
- le diagnostic probable
- la prise en charge complète
- le pronostic vital
- les recommandations

Tu dois uniquement donner des éléments cliniques permettant le raisonnement.

FORMAT OBLIGATOIRE (300–450 mots) :

PATIENT DEMOGRAPHY  
Âge, sexe, contexte médical ou social.

MOTIF D’HOSPITALISATION  
Pourquoi le patient est admis.

ANTÉCÉDENTS  
Uniquement les antécédents utiles (pas trop longs).

EXAMEN PHYSIQUE  
Signes observés + constantes vitales (TA, FC, FR, température, SpO2…)
Sans aucune interprétation.

DONNÉES PARACLINIQUES  
Quelques résultats biologiques ou examens (partiels ou incomplets).

FIN DU CAS

IMPORTANT :
Le texte doit se terminer après les données cliniques.
Ne donne aucune conclusion.
Ne donne aucune solution.
Ne donne aucune réponse.
Le cas clinique doit être construit de manière progressive, basé sur des indices cliniques, permettant à l’étudiant de formuler des hypothèses, d’analyser la situation et de développer son raisonnement clinique sans fournir directement les réponses


Réponds uniquement par le cas clinique.
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
