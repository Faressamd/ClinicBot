import streamlit as st
from clinical_case_generator import generate_clinical_case, _load_secrets
import requests, json, time

st.set_page_config(page_title="🏥 CLINIC-BOT", layout="wide")

st.title("🏥 CLINIC-BOT — Formation clinique intelligente")

# Charger clé API et modèle
groq_api_key, model_name = _load_secrets()

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
    # Réinitialisation de l'état
    st.session_state.clear()
    with st.spinner("Génération du cas clinique en cours..."):
        try:
            case_text = generate_clinical_case(model_name, specialty, severity, groq_api_key)
            st.session_state["current_case"] = case_text
            st.session_state["phase"] = "input"  # Phase de saisie utilisateur
            st.success("✅ Cas clinique généré avec succès !")
        except Exception as e:
            st.error(f"Erreur : {e}")

# --- Affichage du cas clinique ---
if "current_case" in st.session_state:
    st.markdown("## 📋 Cas Clinique")
    st.text_area("Texte du cas", st.session_state["current_case"], height=350, disabled=True)

    # Afficher les champs de réponse seulement si on est en phase d’entrée
    if st.session_state.get("phase") == "input":
        st.markdown("## 🧠 Votre tentative de réponse")

        with st.form("user_response_form", clear_on_submit=False):
            obs = st.text_area("🩺 Observation", height=120, placeholder="Décris ton observation clinique ici...")
            pron = st.text_area("⚕️ Pronostic vital", height=120, placeholder="Évalue le pronostic vital du patient...")
            prise = st.text_area("👩‍⚕️ Prise en charge infirmière", height=120, placeholder="Interventions prioritaires...")
            evalt = st.text_area("📈 Évaluation", height=120, placeholder="Critères de suivi et de réévaluation...")
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

    # Si phase = évaluation → générer la correction AI
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
4️⃣ Termine par un résumé global constructif (points forts et axes d'amélioration).

Format attendu :
### ✅ Correction attendue
...
### 🧩 Évaluation de l'étudiant
- Observation : ...
- Pronostic vital : ...
- Prise en charge infirmière : ...
- Évaluation : ...
### 🏁 Note globale et feedback
...
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

# --- Affichage final du résultat ---
if st.session_state.get("phase") == "result":
    st.markdown("## 🧾 Résultat de l’évaluation")
    st.markdown(st.session_state["evaluation_result"])
    st.markdown("---")

st.caption("Made with ❤️ | CLINIC-BOT | Designed by Nermine El Melki")
