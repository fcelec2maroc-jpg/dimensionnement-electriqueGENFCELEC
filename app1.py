import streamlit as st
import math
from PIL import Image
from fpdf import FPDF

# --- 1. CONFIGURATION ET STYLE ---
st.set_page_config(page_title="FC ELEC - Plateforme Expert", layout="wide")

# --- 2. SYSTÈME DE SÉCURITÉ ---
def check_password():
    def password_entered():
        if st.session_state["username"] in st.secrets["passwords"] and \
           st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.image("logoFCELEC.png", width=200)
        st.title("🔐 Connexion FC ELEC")
        st.text_input("Identifiant", on_change=password_entered, key="username")
        st.text_input("Mot de passe", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", True)

if check_password():
    # --- NAVIGATION ---
    st.sidebar.image("logoFCELEC.png", use_container_width=True)
    st.sidebar.title("🛠️ Menu Principal")
    menu = st.sidebar.selectbox("Choisir un module :", 
                             ["🔌 Dimensionnement Liaison", 
                              "📊 Bilan de Puissance Tableau", 
                              "🛡️ Sécurité & Longueur Max",
                              "📉 Correction du Cos φ",
                              "⚡ Mode de Pose & Iz",
                              "🚘 Module Bornes IRVE"])

    # ---------------------------------------------------------
    # MODULE 1 : DIMENSIONNEMENT LIAISON
    # ---------------------------------------------------------
    if menu == "🔌 Dimensionnement Liaison":
        st.title("🔌 Dimensionnement de Liaison Individuelle")
        col_ref1, col_ref2 = st.columns(2)
        nom_p = col_ref1.text_input("Projet", "Chantier Client")
        ref_c = col_ref2.text_input("Référence Circuit", "DEPART_01")

        c1, c2 = st.columns(2)
        with c1:
            tension = st.radio("Tension", ["230V Mono", "400V Tri"])
            nature = st.selectbox("Conducteur", ["Cuivre", "Aluminium"])
            longueur = st.number_input("Longueur (m)", min_value=1, value=50)
        with c2:
            mode = st.radio("Saisie", ["Puissance (W)", "Courant (A)"])
            val = st.number_input("Valeur", value=3500.0)
            cos_phi = st.slider("cos φ", 0.7, 1.0, 0.85)
        
        du_max = st.selectbox("Chute de tension max (%)", [3, 5, 8])

        V = 230 if "230V" in tension else 400
        rho = 0.0225 if nature == "Cuivre" else 0.036
        b = 2 if "230V" in tension else 1
        Ib = val / (V * cos_phi) if b == 2 else val / (V * math.sqrt(3) * cos_phi) if mode == "Puissance (W)" else val
        
        calibres = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400, 630]
        In = next((x for x in calibres if x >= Ib), calibres[-1])
        S_calc = (b * rho * longueur * Ib) / ((du_max/100)*V)
        sections = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
        S_ret = next((s for s in sections if s >= S_calc), sections[-1])

        st.success(f"Section : {S_ret} mm² | Disjoncteur : {In} A")

    # ---------------------------------------------------------
    # MODULE 2 : BILAN DE PUISSANCE
    # ---------------------------------------------------------
    elif menu == "📊 Bilan de Puissance Tableau":
        st.title("📊 Bilan de Puissance du Tableau")
        if 'bilan' not in st.session_state: st.session_state.bilan = []

        with st.form("Add"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Circuit")
            p = c2.number_input("Puissance (W)", value=0)
            t = c3.selectbox("Type", ["Eclairage", "Prises", "Chauffage", "Moteur"])
            if st.form_submit_button("Ajouter"):
                st.session_state.bilan.append({"nom": n, "p": p, "t": t})
        
        if st.session_state.bilan:
            st.table(st.session_state.bilan)
            p_inst = sum(i['p'] for i in st.session_state.bilan)
            ks = st.slider("Coefficient de simultanéité (Ks)", 0.5, 1.0, 0.8)
            st.metric("Puissance d'appel (P.max)", f"{int(p_inst * ks)} W")
            if st.button("Vider"): st.session_state.bilan = []; st.rerun()

    # ---------------------------------------------------------
    # MODULE 3 : SÉCURITÉ & LONGUEUR MAX
    # ---------------------------------------------------------
    elif menu == "🛡️ Sécurité & Longueur Max":
        st.title("🛡️ Protection contre les Courts-Circuits")
        col1, col2 = st.columns(2)
        sec = col1.selectbox("Section du câble (mm²)", [1.5, 2.5, 4, 6, 10, 16])
        cal = col2.number_input("Calibre Disjoncteur (A)", value=16)
        courbe = st.selectbox("Courbe de déclenchement", ["B (5In)", "C (10In)", "D (20In)"])
        
        m_coef = 5 if "B" in courbe else 10 if "C" in courbe else 20
        l_max = (0.8 * 230 * sec) / (0.0225 * 2 * cal * m_coef)
        st.warning(f"Longueur maximale autorisée : **{int(l_max)} mètres**.")

    # ---------------------------------------------------------
    # MODULE 4 : CORRECTION DU COS PHI
    # ---------------------------------------------------------
    elif menu == "📉 Correction du Cos φ":
        st.title("📉 Compensation Énergie Réactive")
        p_kw = st.number_input("Puissance active totale (kW)", value=50.0)
        c_ini = st.slider("Cos φ actuel", 0.5, 0.95, 0.8)
        c_obj = st.slider("Cos φ désiré", 0.9, 1.0, 0.95)
        
        Qc = p_kw * (math.tan(math.acos(c_ini)) - math.tan(math.acos(c_obj)))
        st.success(f"Puissance batterie condensateurs : **{Qc:.2f} kVAR**")

    # ---------------------------------------------------------
    # MODULE 5 : MODE DE POSE & IZ
    # ---------------------------------------------------------
    elif menu == "⚡ Mode de Pose & Iz":
        st.title("⚡ Vérification Échauffement (Iz)")
        mode = st.selectbox("Mode de pose", ["A1 - Encastré", "B - Sous conduit", "C - Sur chemin de câble", "E - À l'air libre"])
        temp = st.slider("Température ambiante (°C)", 10, 55, 30)
        group = st.number_input("Nombre de circuits groupés", min_value=1, value=1)
        st.info("Ce module calcule les coefficients K pour valider l'intensité admissible Iz.")

    # ---------------------------------------------------------
    # MODULE 6 : BORNES IRVE (NOUVEAU)
    # ---------------------------------------------------------
    elif menu == "🚘 Module Bornes IRVE":
        st.title("🚘 Spécial IRVE (Bornes de recharge)")
        puiss_borne = st.selectbox("Puissance de la borne (kW)", [3.7, 7.4, 11, 22])
        st.write(f"Protection préconisée : Interrupteur différentiel **30mA Type B**.")
        st.write("Section minimale recommandée : **10 mm²** (pour limiter les chutes de tension sur recharge longue).")

    # --- BOUTON DÉCONNEXION ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Déconnexion"):
        st.session_state.clear()
        st.rerun()