import streamlit as st
import requests
from clinical_case_generator import generate_clinical_case, _load_secrets

# ==================================================
# CONFIG PAGE
# ==================================================
st.set_page_config(page_title="🏥 CLINIC-BOT", layout="wide")
st.title("🏥 CLINIC-BOT — Formation clinique intelligente")

# ==================================================
# INITIALISATION SESSION
# ==================================================
if "user_registered" not in st.session_state:
    st.session_state["user_registered"] = False
if "phase" not in st.session_state:
    st.session_state["phase"] = None

# ==================================================
# SECRETS
# ==================================================
groq_api_key, model_name = _load_secrets()
google_script_url = st.secrets["GOOGLE_SCRIPT_URL"]

# ==================================================
# FORMULAIRE IDENTIFICATION (MODE ÉTUDIANT UNIQUEMENT)
# ==================================================
st.markdown("## 👤 Identification de l'étudiant")

with st.form("user_identity_form"):
    st.session_state["nom"] = st.text_input("Nom")
    st.session_state["prenom"] = st.text_input("Prénom")
    st.session_state["classe"] = st.text_input("Classe")
    st.session_state["etablissement_scolaire"] = st.text_input("Établissement scolaire")

    submit_identity = st.form_submit_button("💾 Enregistrer")

# ==================================================
# ENREGISTREMENT GOOGLE SHEET
# ==================================================
if submit_identity:
    if not st.session_state["nom"] or not st.session_state["prenom"]:
        st.warning("⚠️ Nom et prénom sont obligatoires")
    else:
        payload = {
            "nom": st.session_state["nom"],
            "prenom": st.session_state["prenom"],
            "classe": st.session_state["classe"],
            "etablissement_scolaire": st.session_state["etablissement_scolaire"],
        }

        try:
            response = requests.post(google_script_url, json=payload, timeout=10)

            if response.status_code == 200:
                st.session_state["user_registered"] = True
                st.success("✅ Informations enregistrées avec succès")
            else:
                st.error("❌ Erreur lors de l'enregistrement Google Sheet")

        except Exception as e:
            st.error(f"Erreur : {e}")

# ==================================================
# BLOCAGE SI NON ENREGISTRÉ
# ==================================================
if not st.session_state["user_registered"]:
    st.info("ℹ️ Veuillez remplir le formulaire pour accéder à l’application.")
    st.stop()

# ==================================================
# PARAMÈTRES CAS CLINIQUE
# ==================================================
st.sidebar.header("⚙️ Paramètres du cas clinique")

specialty = st.sidebar.selectbox(
    "Spécialité médicale",
    [
        "Médecine interne","Gériatrie","Urgences","Réanimation médicale",
        "Anesthésie-réanimation","SAMU / SMUR","Cardiologie","Pneumologie",
        "Chirurgie cardiaque","Gastro-entérologie","Endocrinologie","Nutrition",
        "Néphrologie","Urologie","Hématologie","Immunologie","Oncologie",
        "Neurologie","Neurochirurgie","Psychiatrie","Rhumatologie","Orthopédie",
        "Gynécologie","Pédiatrie","Néonatologie","Dermatologie","Ophtalmologie",
        "ORL","Stomatologie / Chirurgie maxillo-faciale"
    ]
)

severity = st.sidebar.selectbox("Gravité du cas", ["Mineur", "Modéré", "Critique"], index=1)

# ==================================================
# GÉNÉRATION CAS CLINIQUE
# ==================================================
if st.sidebar.button("🎬 Générer un nouveau cas clinique"):
    st.session_state.pop("current_case", None)
    st.session_state.pop("phase", None)

    with st.spinner("Génération du cas clinique en cours..."):
        try:
            case_text = generate_clinical_case(model_name, specialty, severity, groq_api_key)
            st.session_state["current_case"] = case_text
            st.session_state["phase"] = "input"
            st.success("✅ Cas clinique généré")

        except Exception as e:
            st.error(f"Erreur : {e}")

# ==================================================
# AFFICHAGE CAS + FORMULAIRE RÉPONSE ÉTUDIANT
# ==================================================
if "current_case" in st.session_state:

    st.markdown("## 📋 Cas Clinique")
    st.text_area("Texte du cas", st.session_state["current_case"], height=350, disabled=True)

    if st.session_state["phase"] == "input":

        st.markdown("## 🧠 Votre raisonnement clinique")

        with st.form("user_response_form"):
            obs = st.text_area("🩺 Observation clinique", height=120)
            pron = st.text_area("⚕️ Hypothèses diagnostiques / Pronostic vital", height=120)
            prise = st.text_area("👩‍⚕️ Interventions infirmières proposées", height=120)
            evalt = st.text_area("📈 Comment allez-vous évaluer l’état du patient ?", height=120)

            submit = st.form_submit_button("📤 Soumettre mes réponses")

            if submit:
                if not all([obs, pron, prise, evalt]):
                    st.warning("⚠️ Tous les champs sont obligatoires")
                else:
                    st.session_state["user_responses"] = {
                        "Observation": obs,
                        "Pronostic vital": pron,
                        "Prise en charge infirmière": prise,
                        "Évaluation": evalt,
                    }
                    st.session_state["phase"] = "evaluation"

# ==================================================
# ÉVALUATION IA
# ==================================================
if st.session_state.get("phase") == "evaluation":

    with st.spinner("Évaluation en cours par l'IA..."):

        user_responses = st.session_state["user_responses"]
        case_text = st.session_state["current_case"]

        evaluation_prompt = f"""
Tu es un formateur en soins infirmiers.

Cas clinique :
{case_text}

Réponses de l'étudiant :

Observation : {user_responses['Observation']}
Hypothèses / Pronostic vital : {user_responses['Pronostic vital']}
Interventions infirmières : {user_responses['Prise en charge infirmière']}
Évaluation : {user_responses['Évaluation']}

MISSION :
1. Donne la correction attendue
2. Compare avec les réponses de l'étudiant
3. Donne une note /5 pour chaque section
4. Donne une note finale /20
5. Donne un feedback constructif et pédagogique
"""

        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "Tu es un expert en pédagogie clinique."},
                {"role": "user", "content": evaluation_prompt},
            ],
            "temperature": 0.6,
            "max_tokens": 900,
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90,
        )

        result = response.json()["choices"][0]["message"]["content"]

        st.session_state["evaluation_result"] = result
        st.session_state["phase"] = "result"

        st.success("✅ Évaluation terminée")

# ==================================================
# RÉSULTAT FINAL
# ==================================================
if st.session_state.get("phase") == "result":

    st.markdown("## 🧾 Résultat de l’évaluation")
    st.markdown(st.session_state["evaluation_result"])
