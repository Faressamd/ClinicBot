import streamlit as st
import requests
import json
import time

# ======================================================
# CONFIGURATION GÉNÉRALE
# ======================================================
st.set_page_config(page_title="🏥 CLINIC-BOT", layout="wide")

# Masquer les boutons Streamlit inutiles
hide_streamlit_style = """
<style>
[data-testid="stActionButton"] {display: none !important;}
[title="Share"], [title="GitHub"], [title="Edit"], [title="Favorites"] {display: none !important;}
[data-testid="stToolbar"] button:not(:last-child) {display: none !important;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.title("🏥 CLINIC-BOT — Formation clinique intelligente")

# ======================================================
# CHARGER LES CLÉS SECRÈTES
# ======================================================
def _load_secrets():
    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]
        model_name = st.secrets["MODEL"]
        google_url = st.secrets["GOOGLE_SCRIPT_URL"]
        return groq_api_key, model_name, google_url
    except Exception as e:
        st.error(f"Erreur de chargement des secrets : {e}")
        return None, None, None

groq_api_key, model_name, google_url = _load_secrets()

# ======================================================
# FORMULAIRE D’INSCRIPTION (ENVOI GOOGLE SHEET)
# ======================================================
st.markdown("## 🧾 Formulaire d’inscription")

with st.form("user_info_form"):
    first_name = st.text_input("Prénom")
    last_name = st.text_input("Nom")
    age = st.number_input("Âge", min_value=16, max_value=100, step=1)
    statut = st.radio("Statut :", ["Étudiant", "Nouveau recruté"])
    year_of_study = university = hospital = service = None

    if statut == "Étudiant":
        year_of_study = st.text_input("Année d’étude")
        university = st.text_input("Université")
    else:
        hospital = st.text_input("Hôpital")
        service = st.text_input("Service / Unité")

    experience_level = st.selectbox(
        "Niveau d’expérience en pratique clinique :",
        ["Débutant", "Intermédiaire", "Avancé"]
    )

    comment = st.text_area("Commentaire (facultatif)")

    submitted = st.form_submit_button("📤 Envoyer mes informations")

if submitted:
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "age": age,
        "statut": statut,
        "year_of_study": year_of_study,
        "university": university,
        "hospital": hospital,
        "service": service,
        "experience_level": experience_level,
        "comment": comment,
    }

    try:
        response = requests.post(google_url, data=data)
        if response.status_code == 200:
            st.success("✅ Informations envoyées avec succès au Google Sheet !")
        else:
            st.error(f"Erreur {response.status_code} : {response.text}")
    except Exception as e:
        st.error(f"⚠️ Erreur lors de l’envoi : {e}")

st.divider()

# ======================================================
# PARAMÈTRES DU CAS CLINIQUE
# ======================================================
st.sidebar.header("⚙️ Paramètres du cas clinique")
specialty = st.sidebar.selectbox(
    "Spécialité médicale",
    [
        "Médecine interne", "Gériatrie", "Urgences", "Réanimation médicale",
        "Anesthésie-réanimation", "Cardiologie", "Pneumologie", "Chirurgie cardiaque",
        "Gastro-entérologie", "Endocrinologie", "Néphrologie", "Urologie",
        "Hématologie", "Oncologie", "Neurologie", "Psychiatrie", "Pédiatrie",
        "Orthopédie", "Rhumatologie", "Gynécologie", "Néonatologie"
    ],
)
severity = st.sidebar.selectbox("Gravité du cas", ["Mineur", "Modéré", "Critique"], index=1)

# ======================================================
# GÉNÉRATION DU CAS CLINIQUE
# ======================================================
def generate_clinical_case(model_name, specialty, severity, groq_api_key):
    prompt = f"""
Tu es un formateur en soins infirmiers.
Génère un cas clinique complet et réaliste pour la spécialité : **{specialty}**
Gravité : **{severity}**

Structure :
- Présentation du patient
- Contexte
- Histoire de la maladie
- Observation clinique
- Examens éventuels
(Sans donner la solution)
"""
    api_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "Tu es un expert en formation clinique."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 800,
    }

    response = requests.post(api_url, headers=headers, json=payload, timeout=60)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        st.error(f"Erreur {response.status_code} : {response.text}")
        return None

if st.sidebar.button("🎬 Générer un cas clinique"):
    with st.spinner("Génération du cas en cours..."):
        case_text = generate_clinical_case(model_name, specialty, severity, groq_api_key)
        if case_text:
            st.session_state["current_case"] = case_text
            st.session_state["phase"] = "input"
            st.success("✅ Cas généré avec succès !")

# ======================================================
# AFFICHAGE DU CAS CLINIQUE
# ======================================================
if "current_case" in st.session_state:
    st.markdown("## 📋 Cas clinique")
    st.text_area("Texte du cas", st.session_state["current_case"], height=300, disabled=True)

    if st.session_state.get("phase") == "input":
        st.markdown("## 🧠 Votre réponse")
        with st.form("user_response_form"):
            obs = st.text_area("🩺 Observation", height=120)
            pron = st.text_area("⚕️ Pronostic vital", height=120)
            prise = st.text_area("👩‍⚕️ Prise en charge infirmière", height=120)
            evalt = st.text_area("📈 Évaluation", height=120)
            submit = st.form_submit_button("📤 Soumettre mes réponses")

        if submit:
            if not all([obs, pron, prise, evalt]):
                st.warning("⚠️ Merci de remplir toutes les sections.")
            else:
                st.session_state["user_responses"] = {
                    "Observation": obs,
                    "Pronostic vital": pron,
                    "Prise en charge infirmière": prise,
                    "Évaluation": evalt,
                }
                st.session_state["phase"] = "evaluation"

# ======================================================
# ÉVALUATION IA
# ======================================================
if st.session_state.get("phase") == "evaluation":
    with st.spinner("Évaluation par l’IA en cours..."):
        try:
            user_responses = st.session_state["user_responses"]
            case_text = st.session_state["current_case"]

            evaluation_prompt = f"""
Tu es un formateur en soins infirmiers.
Cas clinique :
{case_text}

Réponses de l’étudiant :
Observation : {user_responses['Observation']}
Pronostic vital : {user_responses['Pronostic vital']}
Prise en charge infirmière : {user_responses['Prise en charge infirmière']}
Évaluation : {user_responses['Évaluation']}

Ta mission :
1️⃣ Donne la correction attendue pour chaque section.
2️⃣ Compare chaque réponse à la correction.
3️⃣ Note sur 5 chaque partie.
4️⃣ Fais un résumé constructif.
"""
            api_url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "Tu es un formateur infirmier expert."},
                    {"role": "user", "content": evaluation_prompt},
                ],
                "temperature": 0.6,
                "max_tokens": 900,
            }

            response = requests.post(api_url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                result = response.json()["choices"][0]["message"]["content"]
                st.session_state["evaluation_result"] = result
                st.session_state["phase"] = "result"
            else:
                st.error(f"Erreur API : {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Erreur : {e}")

# ======================================================
# RÉSULTAT FINAL
# ======================================================
if st.session_state.get("phase") == "result":
    st.markdown("## 🧾 Résultat de l’évaluation")
    st.markdown(st.session_state["evaluation_result"])
    st.divider()

st.caption("Made with ❤️ | CLINIC-BOT | Designed by Nermine El Melki")
