import streamlit as st
import requests
import json
import time
import threading
from clinical_case_generator import generate_clinical_case, _load_secrets

st.set_page_config(page_title="ClinicBot", layout="centered")

# --- Initialisation de l'état ---
if "phase" not in st.session_state:
    st.session_state["phase"] = "intro"

# --- Interface principale ---
st.title("🧠 ClinicBot - Générateur de cas cliniques")

# Sélection de la spécialité
specialite = st.selectbox(
    "Sélectionnez la spécialité médicale :",
    [
        "Cardiologie",
        "Neurologie",
        "Pneumologie",
        "Gastro-entérologie",
        "Endocrinologie",
        "Pédiatrie",
        "Gynécologie",
        "Psychiatrie",
        "Dermatologie",
        "Néphrologie"
    ],
)

# Bouton pour générer un cas
if st.button("🎯 Générer un cas clinique"):
    st.session_state["phase"] = "result"
    with st.spinner("Génération du cas clinique en cours..."):
        try:
            case = generate_clinical_case(specialite)
            st.session_state["evaluation_result"] = case
        except Exception as e:
            st.error(f"Erreur lors de la génération : {e}")

# --- Affichage du résultat ---
if st.session_state.get("phase") == "result":
    st.markdown("## 🧾 Cas clinique généré")
    st.markdown(st.session_state["evaluation_result"])
    st.markdown("---")

    # Minuteur de 30 secondes avant popup
    if "popup_shown" not in st.session_state:
        st.session_state["popup_shown"] = False

        def show_popup_later():
            time.sleep(30)
            st.session_state["popup_shown"] = True
            st.experimental_rerun()

        threading.Thread(target=show_popup_later).start()

# --- Popup Streamlit ---
if st.session_state.get("popup_shown"):
    with st.modal("🧾 Formulaire de retour"):
        st.markdown("### Merci de remplir ce court formulaire 👇")

        # Champs du formulaire
        prenom = st.text_input("Prénom")
        nom = st.text_input("Nom")
        age = st.number_input("Âge", min_value=18, max_value=99, step=1)
        statut = st.selectbox("Statut", ["Étudiant(e)", "Nouveau(elle) recruté(e)"])
        annee_etude = st.text_input("Année d’étude (si étudiant)", disabled=(statut != "Étudiant(e)"))
        universite = st.text_input("Université (si étudiant)", disabled=(statut != "Étudiant(e)"))
        hopital = st.text_input("Hôpital (si nouveau recruté)", disabled=(statut != "Nouveau(elle) recruté(e)"))
        service = st.text_input("Service / Unité hospitalière", disabled=(statut != "Nouveau(elle) recruté(e)"))
        niveau_experience = st.selectbox("Niveau d’expérience clinique", ["Débutant", "Intermédiaire", "Avancé"])
        commentaire = st.text_area("Commentaire (optionnel)", placeholder="Vos remarques ou suggestions...")

        google_script_url = "https://script.google.com/macros/s/AKfycbx6NLXvSJsHH40YJ0KKgabvT2nIaWu809vyWvpQygF5faGcH1vunfuIN8ijCgmOvS9pvw/exec"

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("❌ Fermer"):
                st.session_state["popup_shown"] = False
                st.experimental_rerun()
        with col2:
            if st.button("✅ Envoyer"):
                payload = {
                    "prenom": prenom,
                    "nom": nom,
                    "age": age,
                    "statut": statut,
                    "annee_etude": annee_etude,
                    "universite": universite,
                    "hopital": hopital,
                    "service": service,
                    "niveau_experience": niveau_experience,
                    "commentaire": commentaire,
                }

                try:
                    res = requests.post(google_script_url, json=payload, timeout=10)
                    if res.status_code == 200:
                        st.success("✅ Merci ! Vos informations ont été enregistrées avec succès.")
                        st.session_state["popup_shown"] = False
                        st.experimental_rerun()
                    else:
                        st.error(f"Erreur Google Sheet : {res.status_code}")
                except Exception as e:
                    st.error(f"Erreur d’envoi : {e}")
