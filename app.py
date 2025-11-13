import streamlit as st
from clinical_case_generator import generate_clinical_case, _load_secrets
import requests, json, time, threading

# -------------------------------
# ⚙️ CONFIGURATION GLOBALE
# -------------------------------
st.set_page_config(page_title="🏥 CLINIC-BOT", layout="wide")
st.title("🏥 CLINIC-BOT — Formation clinique intelligente")

groq_api_key, model_name = _load_secrets()

# URL du script Google Apps Script
GOOGLE_SHEET_URL = "https://script.google.com/macros/s/AKfycbx6NLXvSJsHH40YJ0KKgabvT2nIaWu809vyWvpQygF5faGcH1vunfuIN8ijCgmOvS9pvw/exec"


# -------------------------------
# ⚙️ PARAMÈTRES DU CAS CLINIQUE
# -------------------------------
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


# -------------------------------
# 🎬 GÉNÉRATION DU CAS CLINIQUE
# -------------------------------
if st.sidebar.button("🎬 Générer un nouveau cas clinique"):
    st.session_state.clear()
    with st.spinner("Génération du cas clinique en cours..."):
        try:
            case_text = generate_clinical_case(model_name, specialty, severity, groq_api_key)
            st.session_state["current_case"] = case_text
            st.session_state["phase"] = "input"
            st.success("✅ Cas clinique généré avec succès !")
        except Exception as e:
            st.error(f"Erreur : {e}")


# -------------------------------
# 📋 AFFICHAGE DU CAS CLINIQUE
# -------------------------------
if "current_case" in st.session_state:
    st.markdown("## 📋 Cas Clinique")
    st.text_area("Texte du cas", st.session_state["current_case"], height=350, disabled=True)

    # --- Phase 1 : saisie utilisateur ---
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

    # --- Phase 2 : évaluation AI ---
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
                    st.session_state["evaluation_result"] = data["choices"][0]["message"]["content"]
                    st.session_state["phase"] = "result"
                    st.success("✅ Évaluation terminée avec succès.")
                else:
                    st.error(f"Erreur API : {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"Erreur pendant l'évaluation : {e}")


# -------------------------------
# 🧾 AFFICHAGE DU RÉSULTAT FINAL
# -------------------------------
if st.session_state.get("phase") == "result":
    st.markdown("## 🧾 Résultat de l’évaluation")

    if "evaluation_result" in st.session_state:
        st.markdown(st.session_state["evaluation_result"])
    else:
        st.warning("⚠️ Aucun résultat trouvé.")

    st.markdown("---")
    if st.button("🔄 Recommencer"):
        st.session_state.clear()
        st.experimental_rerun()

    # --- Lancer le popup après 30 secondes ---
    if "popup_shown" not in st.session_state:
        st.session_state["popup_shown"] = False

        def show_popup_later():
            time.sleep(30)
            st.session_state["popup_shown"] = True
            st.experimental_rerun()

        threading.Thread(target=show_popup_later).start()


# -------------------------------
# 🧾 FORMULAIRE POPUP (Google Sheet)
# -------------------------------
if st.session_state.get("popup_shown"):
    st.markdown(
        """
        <style>
        .popup {
            position: fixed;
            top: 10%;
            left: 50%;
            transform: translate(-50%, 0);
            background-color: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.3);
            z-index: 1000;
            width: 500px;
        }
        .close-btn {
            position: absolute;
            right: 15px;
            top: 10px;
            cursor: pointer;
            color: red;
            font-weight: bold;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="popup">', unsafe_allow_html=True)
    st.markdown('<div class="close-btn" onclick="window.location.reload()">❌</div>', unsafe_allow_html=True)
    st.markdown("### 🧩 Formulaire d’évaluation de l’expérience")

    with st.form("feedback_form"):
        fname = st.text_input("Prénom")
        lname = st.text_input("Nom")
        age = st.number_input("Âge", min_value=18, max_value=100)
        statut = st.selectbox("Statut", ["Étudiant", "Nouveau recruté"])
        year_study = ""
        university = ""
        hospital = ""
        service = ""

        if statut == "Étudiant":
            year_study = st.text_input("Année d'étude")
            university = st.text_input("Université")
        else:
            hospital = st.text_input("Hôpital")
            service = st.text_input("Service / Unité")

        level = st.selectbox("Niveau d'expérience clinique", ["Débutant", "Intermédiaire", "Avancé"])

        submit_form = st.form_submit_button("📨 Envoyer")

    if submit_form:
        form_data = {
            "FirstName": fname,
            "LastName": lname,
            "Age": age,
            "Statut": statut,
            "YearOfStudy": year_study,
            "University": university,
            "Hospital": hospital,
            "Service": service,
            "ExperienceLevel": level,
        }
        try:
            res = requests.post(GOOGLE_SHEET_URL, json=form_data, timeout=10)
            if res.status_code == 200:
                st.success("✅ Merci ! Vos informations ont été enregistrées avec succès.")
                st.session_state["popup_shown"] = False
            else:
                st.error("❌ Erreur lors de l’envoi du formulaire.")
        except Exception as e:
            st.error(f"Erreur : {e}")

    st.markdown('</div>', unsafe_allow_html=True)


st.caption("Made with ❤️ | CLINIC-BOT | Designed by Nermine El Melki")
