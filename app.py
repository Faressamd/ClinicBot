import streamlit as st
import requests

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="🏥 CLINIC-BOT", layout="centered")
st.title("🏥 CLINIC-BOT")

GOOGLE_SCRIPT_URL = st.secrets["GOOGLE_SCRIPT_URL"]

# ==================================================
# SESSION STATE
# ==================================================
if "user_registered" not in st.session_state:
    st.session_state.user_registered = False

defaults = {
    "nom": "",
    "prenom": "",
    "profil": "Étudiant",
    "etablissement": "",
    "niveau_experience": "",
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==================================================
# FORMULAIRE UTILISATEUR
# ==================================================
st.markdown("## 👤 Identification")

with st.form("user_form"):

    st.text_input("Nom", key="nom")
    st.text_input("Prénom", key="prenom")

    st.selectbox(
        "Profil",
        ["Étudiant", "Infirmier"],
        key="profil"
    )

    # Libellés dynamiques
    etab_label = (
        "Établissement scolaire"
        if st.session_state.profil == "Étudiant"
        else "Établissement professionnel"
    )

    niveau_label = (
        "Classe"
        if st.session_state.profil == "Étudiant"
        else "Années d'expérience"
    )

    st.text_input(etab_label, key="etablissement")

    if st.session_state.profil == "Étudiant":
        st.text_input(niveau_label, key="niveau_experience")
    else:
        st.number_input(
            niveau_label,
            min_value=0,
            max_value=50,
            step=1,
            key="niveau_experience"
        )

    submit = st.form_submit_button("💾 Enregistrer")

# ==================================================
# VALIDATION + GOOGLE SHEET
# ==================================================
if submit:

    if not st.session_state.nom or not st.session_state.prenom:
        st.warning("⚠️ Nom et prénom sont obligatoires")

    elif not st.session_state.etablissement:
        st.warning("⚠️ L’établissement est obligatoire")

    elif st.session_state.niveau_experience in ["", None]:
        st.warning("⚠️ Ce champ est obligatoire")

    else:
        payload = {
            "nom": st.session_state.nom,
            "prenom": st.session_state.prenom,
            "profil": st.session_state.profil,
            "etablissement": st.session_state.etablissement,
            "classe_experience": st.session_state.niveau_experience,
        }

        try:
            response = requests.post(
                GOOGLE_SCRIPT_URL,
                json=payload,
                timeout=10
            )

            if response.status_code == 200 and "success" in response.text:
                st.session_state.user_registered = True
                st.success("✅ Informations enregistrées")
            else:
                st.error("❌ Erreur Google Sheet")
                st.code(response.text)

        except Exception as e:
            st.error(f"Erreur réseau : {e}")

# ==================================================
# BLOCAGE SI NON ENREGISTRÉ
# ==================================================
if not st.session_state.user_registered:
    st.info("ℹ️ Veuillez remplir le formulaire pour continuer.")
    st.stop()

# ==================================================
# APP CONTINUE ICI
# ==================================================
st.success("🎉 Accès autorisé à CLINIC-BOT")
st.markdown("➡️ Ici commence la génération des cas cliniques…")
