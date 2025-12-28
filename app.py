import streamlit as st
import requests
from clinical_case_generator import generate_clinical_case, _load_secrets

# --------------------------------------------------
# CONFIGURATION PAGE
# --------------------------------------------------
st.set_page_config(page_title="🏥 CLINIC-BOT", layout="wide")
st.title("🏥 CLINIC-BOT — Formation clinique intelligente")

# --------------------------------------------------
# CHARGEMENT SECRETS
# --------------------------------------------------
groq_api_key, model_name = _load_secrets()
google_script_url = st.secrets.get("GOOGLE_SCRIPT_URL")

# --------------------------------------------------
# FORMULAIRE IDENTIFICATION UTILISATEUR
# --------------------------------------------------
st.markdown("## 👤 Identification de l'utilisateur")

with st.form("user_identity_form"):
    nom = st.text_input("Nom")
    prenom = st.text_input("Prénom")
    profil = st.selectbox("Profil", ["Étudiant", "Infirmier"])

    classe = ""
    etablissement_scolaire = ""
    etablissement_professionnel = ""
    experience = ""

    if profil == "Étudiant":
        classe = st.text_input("Classe")
        etablissement_scolaire = st.text_input("Établissement scolaire")

    if profil == "Infirmier":
        etablissement_professionnel = st.text_input("Établissement de travail")
        experience = st.number_input(
            "Années d'expérience",
            min_value=0,
            max_value=50,
            step=1
        )

    submit_identity = st.form_submit_button("💾 Enregistrer")

# --------------------------------------------------
# ENREGISTREMENT GOOGLE SHEET
# --------------------------------------------------
if submit_identity:
    if not nom or not prenom:
        st.warning("⚠️ Nom et prénom sont obligatoires")
    else:
        payload = {
            "nom": nom,
            "prenom": prenom,
            "profil": profil,
            "classe": classe,
            "etablissement_scolaire": etablissement_scolaire,
            "etablissement_professionnel": etablissement_professionnel,
            "experience": experience,
        }

        try:
            response = requests.post(
                google_script_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                st.session_state["user_registered"] = True
                st.success("✅ Informations enregistrées avec succès")
            else:
                st.error("❌ Erreur lors de l'enregistrement")
        except Exception as e:
            st.error(f"Erreur : {e}")

# --------------------------------------------------
# BLOCAGE SI UTILISATEUR NON ENREGISTRÉ
# --------------------------------------------------
if not st.session_state.get("user_registered"):
    st.info("ℹ️ Veuillez remplir le formulaire avant de continuer.")
    st.stop()

# --------------------------------------------------
# BARRE LATÉRALE — PARAMÈTRES CAS CLINIQUE
# --------------------------------------------------
st.sidebar.header("⚙️ Paramètres du cas clinique")

specialty = st.sidebar.selectbox(
    "Spécialité médicale",
    [
        "Médecine interne", "Gériatrie", "Urgences", "Réanimation médicale",
        "Anesthésie-réanimation", "SAMU / SMUR", "Cardiologie", "Pneumologie",
        "Chirurgie cardiaque", "Gastro-entérologie", "Endocrinologie",
        "Nutrition", "Néphrologie", "Urologie", "Hématologie", "Immunologie",
        "Oncologie", "Neurologie", "Neurochirurgie", "Psychiatrie",
        "Rhumatologie", "Orthopédie", "Gynécologie", "Pédiatrie",
        "Néonatologie", "Dermatologie", "Ophtalmologie", "ORL",
        "Stomatologie / Chirurgie maxillo-faciale"
    ]
)

severity = st.sidebar.selectbox("Gravité du cas", ["Mineur", "Modéré", "Critique"], index=1)

# --------------------------------------------------
# GÉNÉRATION CAS CLINIQUE
# --------------------------------------------------
if st.sidebar.button("🎬 Générer un nouveau cas clinique"):
    st.session_state.clear()
    st.session_state["user_registered"] = True

    with st.spinner("Génération du cas clinique en cours..."):
        try:
            case_text = generate_clinical_case(
                model_name,
                specialty,
                severity,
                groq_api_key
            )
            st.session_state["current_case"] = case_text
            st.session_state["phase"] = "input"
            st.success("✅ Cas clinique généré")
        except Exception as e:
            st.error(f"Erreur : {e}")

# --------------------------------------------------
# AFFICHAGE CAS + RÉPONSES
# --------------------------------------------------
if "current_case" in st.session_state:
    st.markdown("## 📋 Cas Clinique")
    st.text_area(
        "Texte du cas",
        st.session_state["current_case"],
        height=350,
        disabled=True
    )

    if st.session_state.get("phase") == "input":
        st.markdown("## 🧠 Votre réponse")

        with st.form("user_response_form"):
            obs = st.text_area("🩺 Observation", height=120)
            pron = st.text_area("⚕️ Pronostic vital", height=120)
            prise = st.text_area("👩‍⚕️ Prise en charge infirmière", height=120)
            evalt = st.text_area("📈 Évaluation", height=120)
            submit = st.form_submit_button("📤 Soumettre")

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

# --------------------------------------------------
# ÉVALUATION IA
# --------------------------------------------------
if st.session_state.get("phase") == "evaluation":
    with st.spinner("Évaluation en cours par l'IA..."):
        try:
            user_responses = st.session_state["user_responses"]
            case_text = st.session_state["current_case"]

            evaluation_prompt = f"""
Tu es un formateur en soins infirmiers.

Cas clinique :
{case_text}

Réponses de l'étudiant :
Observation : {user_responses['Observation']}
Pronostic vital : {user_responses['Pronostic vital']}
Prise en charge infirmière : {user_responses['Prise en charge infirmière']}
Évaluation : {user_responses['Évaluation']}

Mission :
1️⃣ Correction attendue
2️⃣ Comparaison
3️⃣ Note /5 par section
4️⃣ Feedback global
"""

            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "Expert en pédagogie clinique"},
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

        except Exception as e:
            st.error(f"Erreur : {e}")

# --------------------------------------------------
# AFFICHAGE RÉSULTAT
# --------------------------------------------------
if st.session_state.get("phase") == "result":
    st.markdown("## 🧾 Résultat de l’évaluation")
    st.markdown(st.session_state["evaluation_result"])
    st.markdown("---")

st.caption("Made with ❤️ | CLINIC-BOT | Designed by Nermine El Melki")
