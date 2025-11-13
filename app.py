import streamlit as st
from clinical_case_generator import generate_clinical_case, _load_secrets
import requests
import json
import time

st.set_page_config(page_title="🏥 CLINIC-BOT", layout="wide")

st.title("🏥 CLINIC-BOT — Formation clinique intelligente")

# Charger les secrets
groq_api_key, model_name = _load_secrets()
google_script_url = st.secrets.get("GOOGLE_SCRIPT_URL", None)

# --- États internes ---
if "popup_time" not in st.session_state:
    st.session_state["popup_time"] = None
if "show_popup" not in st.session_state:
    st.session_state["show_popup"] = False

# --- Barre latérale : paramètres du cas ---
st.sidebar.header("⚙️ Paramètres du cas clinique")
specialty = st.sidebar.selectbox(
    "Spécialité médicale",
    [
        "Détresse respiratoire",
        "Douleur thoracique",
        "Altération de l'état de conscience",
        "Infection sévère",
        "Trauma récent",
        "Urgences cardiaques",
        "Urgences neurologiques",
        "Urgences pédiatriques",
    ],
)
severity = st.sidebar.selectbox("Gravité du cas", ["Mineur", "Modéré", "Critique"], index=1)

# --- Génération du cas clinique ---
if st.sidebar.button("🎬 Générer un nouveau cas clinique"):
    st.session_state.clear()
    with st.spinner("Génération du cas clinique en cours..."):
        try:
            case_text = generate_clinical_case(model_name, specialty, severity, groq_api_key)
            st.session_state["current_case"] = case_text
            st.session_state["phase"] = "input"
            st.session_state["popup_time"] = time.time() + 30  # déclenche le popup après 30s
            st.success("✅ Cas clinique généré avec succès !")
        except Exception as e:
            st.error(f"Erreur : {e}")

# --- Affichage du cas clinique ---
if "current_case" in st.session_state:
    st.markdown("## 📋 Cas Clinique")
    st.text_area("Texte du cas", st.session_state["current_case"], height=350, disabled=True)

    # Vérifie si le popup doit s’afficher après 30s
    if (
        st.session_state.get("popup_time")
        and time.time() > st.session_state["popup_time"]
        and not st.session_state["show_popup"]
    ):
        st.session_state["show_popup"] = True

    # --- Popup après 30 secondes ---
    if st.session_state.get("show_popup"):
        with st.modal("🧾 Formulaire d’inscription"):
            st.markdown("### Merci de remplir ce formulaire avant de continuer 👇")

            with st.form("popup_form"):
                fname = st.text_input("Prénom")
                lname = st.text_input("Nom")
                age = st.number_input("Âge", min_value=18, max_value=99, step=1)
                statut = st.radio("Statut", ["Étudiant", "Nouveau recruté"])
                year = university = hospital = service = ""
                if statut == "Étudiant":
                    year = st.text_input("Année d’étude")
                    university = st.text_input("Université")
                else:
                    hospital = st.text_input("Hôpital")
                    service = st.text_input("Service / Unité")
                exp_level = st.selectbox(
                    "Niveau d’expérience en pratique clinique",
                    ["Débutant", "Intermédiaire", "Avancé"],
                )
                submit_popup = st.form_submit_button("📤 Envoyer")

            if submit_popup:
                if not fname or not lname:
                    st.warning("⚠️ Merci de remplir le prénom et le nom.")
                else:
                    data = {
                        "FirstName": fname,
                        "LastName": lname,
                        "Age": age,
                        "Statut": statut,
                        "Year": year,
                        "University": university,
                        "Hospital": hospital,
                        "Service": service,
                        "Experience": exp_level,
                    }
                    try:
                        if google_script_url:
                            res = requests.post(google_script_url, data=data)
                            if res.status_code == 200:
                                st.success("✅ Données envoyées avec succès à Google Sheet !")
                                st.session_state["show_popup"] = False
                            else:
                                st.error(f"Erreur d’envoi : {res.status_code}")
                        else:
                            st.error("🚨 GOOGLE_SCRIPT_URL manquant dans secrets.toml")
                    except Exception as e:
                        st.error(f"Erreur : {e}")

    # --- Phase input ---
    if st.session_state.get("phase") == "input":
        st.markdown("## 🧠 Votre tentative de réponse")
        with st.form("user_response_form", clear_on_submit=False):
            obs = st.text_area("🩺 Observation", height=120)
            pron = st.text_area("⚕️ Pronostic vital", height=120)
            prise = st.text_area("👩‍⚕️ Prise en charge infirmière", height=120)
            evalt = st.text_area("📈 Évaluation", height=120)
            submit = st.form_submit_button("📤 Soumettre mes réponses")

        if submit:
            if not all([obs, pron, prise, evalt]):
                st.warning("⚠️ Merci de remplir toutes les sections avant de soumettre.")
            else:
                st.session_state["user_responses"] = {
                    "Observation": obs,
                    "Pronostic vital": pron,
                    "Prise en charge infirmière": prise,
                    "Évaluation": evalt,
                }
                st.session_state["phase"] = "evaluation"

    elif st.session_state.get("phase") == "evaluation":
        with st.spinner("Évaluation en cours par l'IA..."):
            try:
                user_responses = st.session_state["user_responses"]
                case_text = st.session_state["current_case"]

                evaluation_prompt = f"""
Tu es un formateur en soins infirmiers.
Voici un cas clinique :
{case_text}

L'étudiant a répondu :
Observation : {user_responses['Observation']}
Pronostic vital : {user_responses['Pronostic vital']}
Prise en charge infirmière : {user_responses['Prise en charge infirmière']}
Évaluation : {user_responses['Évaluation']}

Ta mission :
1️⃣ Donne la correction attendue pour chaque section.  
2️⃣ Compare chaque réponse de l'étudiant à la correction.  
3️⃣ Donne une note /5 pour chaque section.  
4️⃣ Termine par un résumé global constructif.
"""

                api_url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "Tu es un expert en pédagogie clinique."},
                        {"role": "user", "content": evaluation_prompt},
                    ],
                    "temperature": 0.6,
                    "max_tokens": 900,
                }

                response = requests.post(api_url, headers=headers, json=payload, timeout=90)
                if response.status_code == 200:
                    data = response.json()
                    result = data["choices"][0]["message"]["content"]
                    st.session_state["evaluation_result"] = result
                    st.session_state["phase"] = "result"
                    st.success("✅ Évaluation terminée avec succès.")
                else:
                    st.error(f"Erreur API : {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Erreur pendant l'évaluation : {e}")

# --- Résultat final ---
if st.session_state.get("phase") == "result":
    st.markdown("## 🧾 Résultat de l’évaluation")
    st.markdown(st.session_state["evaluation_result"])
    st.markdown("---")

st.caption("Made with ❤️ | CLINIC-BOT | Designed by Nermine El Melki")
