import streamlit as st
import requests
from clinical_case_generator import generate_clinical_case, _load_secrets

# ==================================================
# CONFIG PAGE
# ==================================================
st.set_page_config(page_title="🏥 CLINIC-BOT", layout="wide")
st.title("NursaMind AI — L’intelligence au service du raisonnement clinique")

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

submit_identity = False

if not st.session_state["user_registered"]:

    st.markdown("## 👤 Identification de l'étudiant")

    with st.form("user_identity_form"):
        st.session_state["classe"] = st.text_input("Classe")
        st.session_state["etablissement_Universitaire"] = st.text_input("Établissement Universitaire")

        submit_identity = st.form_submit_button("💾 Enregistrer")

# ==================================================
# ENREGISTREMENT GOOGLE SHEET
# ==================================================
if submit_identity:
    if not st.session_state["classe"] or not st.session_state["etablissement_Universitaire"]:
        st.warning("⚠️ Classe et établissement Universitaire sont obligatoires")
    else:
        payload = {
            "classe": st.session_state["classe"],
            "etablissement_scolaire": st.session_state["etablissement_Universitaire"],
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
# QUESTIONNAIRE PRÉ-TEST (OBLIGATOIRE)
# ==================================================

st.markdown("## 📋 Questionnaire Pré-test obligatoire")

st.markdown("""
Ce questionnaire vise à évaluer le niveau initial de jugement clinique des étudiants
avant l’utilisation de l’application basée sur l’intelligence artificielle.
""")

st.markdown("👉 Cliquez ici pour accéder au questionnaire :")

st.markdown("[Accéder au Pré-test](https://docs.google.com/forms/d/e/1FAIpQLSdnmCZnWPxyJG0xqtr-PDJFln_1fZ0VJSOChiMIm3_3Apegtg/formResponse?pli=1)")

pretest_done = st.checkbox("J’ai complété le questionnaire Pré-test")

# ==================================================
# GÉNÉRATION CAS CLINIQUE
# ==================================================
if pretest_done and st.sidebar.button("🎬 Générer un nouveau cas clinique"):
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

            # ==============================
            # 1. HYPOTHÈSES PAR PRIORITÉ
            # ==============================
            st.markdown("### 1️⃣ Hypothèses diagnostiques par priorité")
            hyp1 = st.text_area("Hypothèse prioritaire (la plus urgente)", height=90)
            hyp2 = st.text_area("Deuxième hypothèse", height=90)
            hyp3 = st.text_area("Troisième hypothèse", height=90)

            # ==============================
            # 2. COLLECTE DES DONNÉES
            # ==============================
            st.markdown("### 2️⃣ Collecte des données")
            data_collection = st.text_area("Examens complémentaires / Informations à rechercher", height=120)

            # ==============================
            # 3. INTERVENTIONS INFIRMIÈRES
            # ==============================
            st.markdown("### 3️⃣ Interventions infirmières ")
            nursing_actions = st.text_area("Quelles actions faites-vous immédiatement ?", height=140)

            # ==============================
            # 4. ÉVALUATION
            # ==============================
            st.markdown("### 4️⃣ Évaluation")
            evaluation = st.text_area("Quels paramètres allez-vous surveiller ?", height=120)

            submit = st.form_submit_button("📤 Soumettre mes réponses")

            if submit:
                if not all([hyp1, data_collection, nursing_actions, evaluation]):  # Hypothèse 3 non obligatoire
                    st.warning("⚠️ Tous les champs principaux sont obligatoires")
                else:
                    st.session_state["user_responses"] = {
                        "Hypothèse 1": hyp1,
                        "Hypothèse 2": hyp2,
                        "Hypothèse 3": hyp3 if hyp3 else "Non renseignée",
                        "Collecte des données": data_collection,
                        "Interventions infirmières": nursing_actions,
                        "Évaluation": evaluation,
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
Tu es un formateur clinique expérimenté en soins infirmiers.

Ton rôle est d'évaluer OBJECTIVEMENT les réponses de l'étudiant en fonction de ce qu'il a réellement écrit.

Cas clinique :
{case_text}

Réponses de l'étudiant :

Hypothèse 1 (prioritaire) : {user_responses['Hypothèse 1']}
Hypothèse 2 : {user_responses['Hypothèse 2']}
Hypothèse 3 : {user_responses['Hypothèse 3']}

Collecte des données : {user_responses['Collecte des données']}

Interventions infirmières : {user_responses['Interventions infirmières']}

Évaluation : {user_responses['Évaluation']}

RÈGLES IMPORTANTES POUR L'ÉVALUATION :
- Ne donne pas une note générique
- Analyse ce que l'étudiant a réellement écrit
- Si la réponse est partielle → donne une note partielle
- Si la réponse est logique mais incomplète → valorise le raisonnement
- Si la priorité clinique est fausse → explique pourquoi
- Si une partie est vide ou très faible → note faible mais reste pédagogique

FORMAT DE RÉPONSE OBLIGATOIRE :

1️⃣ Correction attendue (version formateur claire et structurée)

2️⃣ Analyse des réponses de l'étudiant
- Hypothèses diagnostiques : (analyse précise)
- Collecte des données : (analyse précise)
- Interventions infirmières : (analyse précise)
- Évaluation : (analyse précise)

3️⃣ Notation détaillée
Hypothèses diagnostiques : X /5
Collecte des données : X /5
Interventions infirmières : X /5
Évaluation : X /5

4️⃣ Note finale : X /20

5️⃣ Feedback pédagogique
Donne un feedback clair, encourageant mais honnête, comme un vrai formateur clinique.
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

    # ==================================================
    # QUESTIONNAIRE POST-TEST
    # ==================================================

    st.markdown("---")
    st.markdown("## 📋 Questionnaire Post-test")

    st.markdown("""
Ce questionnaire vise à évaluer l’amélioration du jugement clinique des étudiants
après l’utilisation de l’application basée sur l’intelligence artificielle.
""")

    st.markdown("👉 Cliquez ici pour accéder au questionnaire :")

    st.markdown("[Accéder au Post-test](https://docs.google.com/forms/d/e/1FAIpQLSf4CbpAPMKK2gQ5E02Va3jX6Cj_vNT3hKUmV_TVcnaO8pXpWQ/viewform)")
