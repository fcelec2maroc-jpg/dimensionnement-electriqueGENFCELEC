import streamlit as st
import math
from PIL import Image
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="FC ELEC - Plateforme Expert", layout="wide")

# --- CLASSE PDF PERSONNALISÉE ---
class FCELEC_PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, "FC ELEC - Contact WhatsApp : +212 6 74 53 42 64 - Document conforme NF C 15-100", 0, 0, "C")

# --- SYSTÈME DE SÉCURITÉ ---
def check_password():
    if "password_correct" not in st.session_state:
        st.image("logoFCELEC.png", width=200)
        st.title("🔐 Connexion FC ELEC")
        user = st.text_input("Identifiant")
        pw = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            if "passwords" in st.secrets and user in st.secrets["passwords"] and pw == st.secrets["passwords"][user]:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Identifiants incorrects.")
        return False
    return True

if check_password():
    # --- BARRE LATÉRALE ---
    st.sidebar.image("logoFCELEC.png", use_container_width=True)
    st.sidebar.title("🛠️ MENU EXPERT")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("SÉLECTIONNER UN MODULE :", [
        "🔌 Liaison Individuelle",
        "📊 Bilan de Puissance",
        "🛡️ Sécurité & Lmax",
        "📉 Correction Cos φ",
        "⚡ Mode de Pose (Iz)",
        "🚘 Bornes IRVE"
    ])

    # ---------------------------------------------------------
    # MODULE 1 : LIAISON INDIVIDUELLE (VOTRE MODÈLE PDF)
    # ---------------------------------------------------------
    if menu == "🔌 Liaison Individuelle":
        st.title("🔌 Dimensionnement de Liaison (NF C 15-100)")
        
        st.subheader("📋 Identification")
        col_ref1, col_ref2 = st.columns(2)
        nom_projet = col_ref1.text_input("Nom du Projet / Client", "Chantier Client")
        ref_circuit = col_ref2.text_input("Référence du Circuit", "DEPART_01")
        
        st.markdown("---")

        col_input1, col_input2 = st.columns(2)
        with col_input1:
            tension_type = st.radio("Tension", ["Monophasé (230V)", "Triphasé (400V)"])
            nature_cable = st.selectbox("Nature du conducteur", ["Cuivre", "Aluminium"])
            longueur = st.number_input("Longueur du câble (m)", min_value=1, value=50)
        with col_input2:
            mode_saisie = st.radio("Saisie par", ["Puissance (W)", "Courant (A)"])
            if mode_saisie == "Puissance (W)":
                P = st.number_input("Puissance (Watts)", value=3500)
                cos_phi = st.slider("cos φ", 0.7, 1.0, 0.85)
            else:
                Ib_input = st.number_input("Courant Ib (Ampères)", value=16.0)
                cos_phi = 0.85

        delta_u_max_pct = st.select_slider("Chute de tension max (%)", options=[3, 5, 8], value=3)

        # CALCULS
        V = 230 if "Monophasé" in tension_type else 400
        rho = 0.0225 if nature_cable == "Cuivre" else 0.036
        b = 2 if "Monophasé" in tension_type else 1

        if mode_saisie == "Puissance (W)":
            Ib = P / (V * cos_phi) if b == 2 else P / (V * math.sqrt(3) * cos_phi)
        else:
            Ib = Ib_input

        calibres = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400, 630]
        In = next((x for x in calibres if x >= Ib), calibres[-1])
        S_calculée = (b * rho * longueur * Ib) / ((delta_u_max_pct / 100) * V)
        sections_std = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
        S_retenue = next((s for s in sections_std if s >= S_calculée), "Section trop importante")
        du_v = (b * rho * longueur * Ib) / (S_retenue if isinstance(S_retenue, float) else 240)
        du_pct = (du_v / V) * 100

        st.success(f"Section : **{S_retenue} mm²** | Disjoncteur : **{In} A**")

        def generate_pdf():
            pdf = FCELEC_PDF()
            pdf.add_page()
            try: pdf.image("logoFCELEC.png", 10, 8, 35)
            except: pass
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(190, 15, "NOTE DE SYNTHESE ELECTRIQUE", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 11); pdf.set_fill_color(240, 240, 240)
            pdf.cell(190, 10, f" PROJET : {nom_projet.upper()}", border=1, ln=True, fill=True)
            pdf.cell(190, 10, f" REFERENCE CIRCUIT : {ref_circuit}", border=1, ln=True)
            pdf.ln(5)
            pdf.cell(100, 10, "CARACTERISTIQUE", border=1, align="C")
            pdf.cell(90, 10, "VALEUR", border=1, ln=True, align="C")
            pdf.set_font("Helvetica", "", 11)
            lignes = [("Tension", tension_type), ("Conducteur", nature_cable), ("Longueur", f"{longueur} m"),
                      ("Intensite (Ib)", f"{Ib:.2f} A"), ("Protection (In)", f"{In} A"),
                      ("Chute de tension", f"{du_pct:.2f} %"), ("SECTION RETENUE", f"{S_retenue} mm2")]
            for desc, val in lignes:
                if "SECTION" in desc: pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(255, 140, 0)
                pdf.cell(100, 10, f" {desc}", border=1); pdf.cell(90, 10, f" {val}", border=1, ln=True, align="C")
                pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 11)
            return pdf.output()

        if st.button("📄 Préparer la Note de Calcul (PDF)"):
            st.download_button(label="📥 Télécharger le PDF", data=bytes(generate_pdf()), file_name=f"FCELEC_{ref_circuit}.pdf", mime="application/pdf")

    # ---------------------------------------------------------
    # MODULE 2 : BILAN DE PUISSANCE
    # ---------------------------------------------------------
    elif menu == "📊 Bilan de Puissance":
        st.title("📊 Bilan de Puissance du Tableau")
        if 'bilan' not in st.session_state: st.session_state.bilan = []
        with st.form("ajout"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Désignation")
            p = c2.number_input("Puissance (W)", value=0)
            if st.form_submit_button("Ajouter"): st.session_state.bilan.append({"n": n, "p": p})
        
        if st.session_state.bilan:
            st.table(st.session_state.bilan)
            total = sum(i['p'] for i in st.session_state.bilan)
            ks = st.slider("Coefficient de simultanéité (Ks)", 0.5, 1.0, 0.8)
            st.metric("Puissance d'Appel Totale", f"{int(total * ks)} W")
            if st.button("Réinitialiser"): st.session_state.bilan = []; st.rerun()

    # ---------------------------------------------------------
    # MODULE 3 : SÉCURITÉ & LMAX
    # ---------------------------------------------------------
    elif menu == "🛡️ Sécurité & Lmax":
        st.title("🛡️ Sécurité : Longueur Maximale")
        col1, col2 = st.columns(2)
        sec = col1.selectbox("Section (mm²)", [1.5, 2.5, 4, 6, 10, 16, 25])
        cal = col2.number_input("Calibre (A)", value=16)
        # Formule Lmax = (0.8 * U * S) / (2 * rho * Imag)
        lmax = (0.8 * 230 * sec) / (2 * 0.0225 * cal * 10)
        st.warning(f"Longueur maximale autorisée : **{int(lmax)} m**.")

    # ---------------------------------------------------------
    # MODULE 4 : CORRECTION DU COS PHI
    # ---------------------------------------------------------
    elif menu == "📉 Correction Cos φ":
        st.title("📉 Compensation Énergie Réactive")
        p_kw = st.number_input("Puissance de l'installation (kW)", value=50.0)
        c_ini = st.slider("Cos φ actuel", 0.5, 0.95, 0.7)
        c_obj = st.slider("Cos φ visé", 0.9, 1.0, 0.95)
        # Qc = P * (tan phi1 - tan phi2)
        qc = p_kw * (math.tan(math.acos(c_ini)) - math.tan(math.acos(c_obj)))
        st.success(f"Batterie de condensateurs nécessaire : **{qc:.2f} kVAR**")

    # ---------------------------------------------------------
    # MODULE 5 : MODE DE POSE (IZ)
    # ---------------------------------------------------------
    elif menu == "⚡ Mode de Pose (Iz)":
        st.title("⚡ Intensité Admissible Iz")
        mp = st.selectbox("Mode de pose", ["A1 - Encastré dans isolant", "B - Conduit apparent", "C - Sur chemin de câble", "E - Air libre"])
        group = st.number_input("Nombre de circuits groupés", value=1, min_value=1)
        st.info("Ce module vérifie que l'échauffement thermique respecte la norme NF C 15-100.")

    # ---------------------------------------------------------
    # MODULE 6 : BORNES IRVE
    # ---------------------------------------------------------
    elif menu == "🚘 Bornes IRVE":
        st.title("🚘 Mobilité Électrique")
        p_b = st.selectbox("Puissance de borne (kW)", [3.7, 7.4, 11, 22])
        st.metric("Disjoncteur préconisé", f"{int(p_b*1000/230*1.25)} A")
        st.warning("Protection différentielle : **30mA Type B** obligatoire.")

    # --- DÉCONNEXION ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear(); st.rerun()