import streamlit as st
import requests
from clinical_case_generator import generate_clinical_case, _load_secrets

# ==================================================
# CONFIG PAGE
# ==================================================
st.set_page_config(page_title="🏥 CLINIC-BOT", layout="wide")
st.title("🏥 CLINIC-BOT — Formation clinique intelligente")

# ==================================================
# SESSION STATE GLOBAL
# ==================================================
if "user_registered" not in st.session_state:
    st.session_state.user_registered = False

if "phase" not in st.session_state:
    st.session_state.phase = None

# ==================================================
# INIT FORM STATE
# ==================================================
defaults = {
    "nom": "",
    "prenom": "",
    "profil": "Étudiant",
    "classe": "",
    "etablissement_scolaire": "",
    "etablissement_professionnel": "",
    "experience": 0,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==================================================
# SECRETS
# ==================================================
groq_api_key, model_name = _load_secrets()
google_script_url = st.secrets["GOOGLE_SCRIPT_URL"]

# ==================================================
# FORMULAIRE UTILISATEUR
# ==================================================
st.markdown("## 👤 Identification de l'utilisateur")

with st.form("user_identity_form"):

    st.text_input("Nom", key="nom")
    st.text_input("Prénom", key="prenom")

    st.selectbox(
        "Profil",
        ["Étudiant", "Infirmier"],
        key="profil"
    )

    if st.session_state.profil == "Étudiant":

        # reset infirmier
        st.session_state.etablissement_professionnel = ""
        st.session_state.experience = 0

        st.text_input("Classe", key="classe")
        st.text_input("Établissement scolaire", key="etablissement_scolaire")

    else:  # Infirmier

        # reset étudiant
        st.session_state.classe = ""
        st.session_state.etablissement_scolaire = ""

        st.text_input(
            "Établissement de travail",
            key="etablissement_professionnel"
        )

        st.number_input(
            "Années d'expérience",
            min_value=0,
            max_value=50,
            step=1,
            key="experience"
        )

    submit_identity = st.form_submit_button("💾 Enregistrer")

# ==================================================
# ENREGISTREMENT GOOGLE SHEET
# ==================================================
if submit_identity:

    if not st.session_state.nom or not st.session_state.prenom:
        st.warning("⚠️ Nom et prénom sont obligatoires")

    elif st.session_state.profil == "Étudiant" and (
        not st.session_state.classe
        or not st.session_state.etablissement_scolaire
    ):
        st.warning("⚠️ Classe et établissement scolaire obligatoires")

    elif st.session_state.profil == "Infirmier" and (
        not st.session_state.etablissement_professionnel
    ):
        st.warning("⚠️ Établissement de travail obligatoire")

    else:
        payload = {
            "nom": st.session_state.nom,
            "prenom": st.session_state.prenom,
            "profil": st.session_state.profil,
            "classe": st.session_state.classe,
            "etablissement_scolaire": st.session_state.etablissement_scolaire,
            "etablissement_professionnel": st.session_state.etablissement_professionnel,
            "experience": st.session_state.experience,
        }

        try:
            response = requests.post(
                google_script_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200 and "success" in response.text:
                st.session_state.user_registered = True
                st.success("✅ Informations enregistrées avec succès")
            else:
                st.error("❌ Erreur lors de l'enregistrement Google Sheet")
                st.code(response.text)

        except Exception as e:
            st.error(f"Erreur réseau : {e}")

# ==================================================
# BLOCAGE APP SI NON ENREGISTRÉ
# ==================================================
if not st.session_state.user_registered:
    st.info("ℹ️ Veuillez remplir le formulaire pour accéder à l’application.")
    st.stop()

# ==================================================
# SIDEBAR — PARAMÈTRES CAS CLINIQUE
# ==================================================
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

severity = st.sidebar.selectbox(
    "Gravité du cas",
    ["Mineur", "Modéré", "Critique"],
    index=1
)

# ==================================================
# GÉNÉRATION CAS CLINIQUE
# ==================================================
if st.sidebar.button("🎬 Générer un nouveau cas clinique"):
    st.session_state.pop("current_case", None)
    st.session_state.phase = "input"

    with st.spinner("Génération du cas clinique en cours..."):
        case_text = generate_clinical_case(
            model_name,
            specialty,
            severity,
            groq_api_key
        )
        st.session_state.current_case = case_text
        st.success("✅ Cas clinique généré")

# ==================================================
# AFFICHAGE CAS + RÉPONSES
# ==================================================
if "current_case" in st.session_state:

    st.markdown("## 📋 Cas Clinique")
    st.text_area(
        "Texte du cas",
        st.session_state.current_case,
        height=350,
        disabled=True
    )

    if st.session_state.phase == "input":

        with st.form("user_response_form"):
            obs = st.text_area("🩺 Observation", height=120)
            pron = st.text_area("⚕️ Pronostic vital", height=120)
            prise = st.text_area("👩‍⚕️ Prise en charge infirmière", height=120)
            evalt = st.text_area("📈 Évaluation", height=120)

            submit = st.form_submit_button("📤 Soumettre mes réponses")

        if submit:
            if not all([obs, pron, prise, evalt]):
                st.warning("⚠️ Tous les champs sont obligatoires")
            else:
                st.session_state.user_responses = {
                    "Observation": obs,
                    "Pronostic vital": pron,
                    "Prise en charge infirmière": prise,
                    "Évaluation": evalt,
                }
                st.session_state.phase = "evaluation"

# ==================================================
# ÉVALUATION IA
# ==================================================
if st.session_state.phase == "evaluation":

    with st.spinner("Évaluation en cours par l'IA..."):

        case_text = st.session_state.current_case
        r = st.session_state.user_responses

        prompt = f"""
Tu es un formateur expert en soins infirmiers.

Cas clinique :
{case_text}

Réponses :
Observation : {r['Observation']}
Pronostic vital : {r['Pronostic vital']}
Prise en charge infirmière : {r['Prise en charge infirmière']}
Évaluation : {r['Évaluation']}

Donne :
1. Correction attendue
2. Comparaison
3. Note /5 par section
4. Feedback global
"""

        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "Tu es un expert en pédagogie clinique."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6,
            "max_tokens": 900
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=90
        )

        st.session_state.evaluation_result = response.json()["choices"][0]["message"]["content"]
        st.session_state.phase = "result"
        st.success("✅ Évaluation terminée")

# ==================================================
# RÉSULTAT FINAL
# ==================================================
if st.session_state.phase == "result":
    st.markdown("## 🧾 Résultat de l’évaluation")
    st.markdown(st.session_state.evaluation_result)

st.caption("Made with ❤️ | CLINIC-BOT")
