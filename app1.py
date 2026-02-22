import streamlit as st
import math
from PIL import Image
from fpdf import FPDF

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FC ELEC - Plateforme Expert", layout="wide")

# --- CLASSE PDF PERSONNALISÉE (AVEC WHATSAPP) ---
class FCELEC_PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        # Votre numéro WhatsApp en pied de page
        self.cell(0, 10, "FC ELEC - Contact WhatsApp : +212 6 74 53 42 64 - Document conforme NF C 15-100", 0, 0, "C")

# --- SYSTÈME DE SÉCURITÉ ---
def check_password():
    def password_entered():
        if "passwords" in st.secrets:
            if st.session_state["username"] in st.secrets["passwords"] and \
               st.session_state["password"] == st.secrets["passwords"][st.session_state["username"]]:
                st.session_state["password_correct"] = True
                del st.session_state["password"] 
                del st.session_state["username"]
            else:
                st.session_state["password_correct"] = False
    
    if "password_correct" not in st.session_state:
        st.image("logoFCELEC.png", width=200)
        st.title("🔐 Accès FC ELEC")
        st.text_input("Identifiant", key="username")
        st.text_input("Mot de passe", type="password", key="password")
        if st.button("Se connecter"):
            password_entered()
            st.rerun()
        return False
    return True

if check_password():
    # --- NAVIGATION LATÉRALE ---
    st.sidebar.image("logoFCELEC.png", use_container_width=True)
    st.sidebar.title("🛠️ MENU EXPERT")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.radio("SÉLECTIONNER UN MODULE :", [
        "🔌 Liaison Individuelle",
        "📊 Bilan de Puissance",
        "🛡️ Sécurité & Lmax",
        "📉 Correction Cos φ",
        "⚡ Mode de Pose (Iz)",
        "🚘 Bornes IRVE",
        "☀️ Solaire PV",
        "📐 Calcul de Terre"
    ])

    # ---------------------------------------------------------
    # MODULE 1 : LIAISON INDIVIDUELLE (VOTRE MODÈLE PDF INCLUS)
    # ---------------------------------------------------------
    if menu == "🔌 Liaison Individuelle":
        st.title("🔌 Dimensionnement de Liaison (NF C 15-100)")
        
        st.subheader("📋 Identification")
        col_ref1, col_ref2 = st.columns(2)
        with col_ref1:
            nom_projet = st.text_input("Nom du Projet / Client", "Chantier Client")
        with col_ref2:
            ref_circuit = st.text_input("Référence du Circuit", "DEPART_01")
        
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

        # --- CALCULS TECHNIQUES ---
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
        S_retenue = next((s for s in sections_std if s >= S_calculée), sections_std[-1])
        du_v = (b * rho * longueur * Ib) / S_retenue
        du_pct = (du_v / V) * 100

        # Affichage des résultats à l'écran
        st.markdown("### 📊 Résultats")
        r1, r2, r3 = st.columns(3)
        r1.metric("Courant Ib", f"{Ib:.2f} A")
        r2.metric("Protection In", f"{In} A")
        r3.metric("Section Retenue", f"{S_retenue} mm²")

        # --- VOTRE CODE PDF (SYNTHÈSE SANS DÉTAILS) ---
        def generate_pdf():
            pdf = FCELEC_PDF()
            pdf.add_page()
            try:
                pdf.image("logoFCELEC.png", 10, 8, 35)
            except:
                pass
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(190, 15, "NOTE DE SYNTHESE ELECTRIQUE", ln=True, align="C")
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(190, 10, f" PROJET : {nom_projet.upper()}", border=1, ln=True, fill=True)
            pdf.cell(190, 10, f" REFERENCE CIRCUIT : {ref_circuit}", border=1, ln=True)
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(100, 10, "CARACTERISTIQUE", border=1, align="C")
            pdf.cell(90, 10, "VALEUR", border=1, ln=True, align="C")
            pdf.set_font("Helvetica", "", 11)
            lignes = [
                ("Tension de service", f"{tension_type}"),
                ("Nature du conducteur", f"{nature_cable}"),
                ("Longueur de liaison", f"{longueur} m"),
                ("Intensite d'emploi (Ib)", f"{Ib:.2f} A"),
                ("Protection conseillee (In)", f"{In} A"),
                ("Chute de tension reelle", f"{du_pct:.2f} %"),
                ("SECTION DE CABLE RETENUE", f"{S_retenue} mm2")
            ]
            for desc, val in lignes:
                if "SECTION" in desc:
                    pdf.set_font("Helvetica", "B", 12)
                    pdf.set_text_color(255, 140, 0)
                pdf.cell(100, 10, f" {desc}", border=1)
                pdf.cell(90, 10, f" {val}", border=1, ln=True, align="C")
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 11)
            pdf.ln(15)
            pdf.set_font("Helvetica", "I", 8)
            pdf.cell(190, 10, "Document genere par FC ELEC conforme a la norme NF C 15-100", align="C")
            return pdf.output()

        st.markdown("---")
        if st.button("📄 Préparer la Note de Calcul (PDF)"):
            pdf_bytes = generate_pdf()
            st.download_button(
                label="📥 Télécharger le PDF",
                data=bytes(pdf_bytes),
                file_name=f"FCELEC_{ref_circuit}.pdf",
                mime="application/pdf"
            )

    # ---------------------------------------------------------
    # MODULE 2 : BILAN DE PUISSANCE
    # ---------------------------------------------------------
    elif menu == "📊 Bilan de Puissance":
        st.title("📊 Bilan de Puissance du Tableau")
        st.info("Module pour calculer la puissance totale appelée (Ku / Ks).")

    # ---------------------------------------------------------
    # MODULE 3 : SÉCURITÉ & LMAX
    # ---------------------------------------------------------
    elif menu == "🛡️ Sécurité & Lmax":
        st.title("🛡️ Protection Magnétique (Lmax)")
        st.write("Calcul de la longueur maximale pour garantir le déclenchement du disjoncteur.")
        sec_l = st.selectbox("Section câble (mm²)", [1.5, 2.5, 4, 6, 10, 16, 25])
        cal_l = st.number_input("Calibre (A)", value=16)
        l_max = (0.8 * 230 * sec_l) / (0.0225 * 2 * cal_l * 10)
        st.warning(f"La longueur maximale recommandée est de **{int(l_max)} mètres**.")

    # ---------------------------------------------------------
    # MODULE 7 : SOLAIRE PV
    # ---------------------------------------------------------
    elif menu == "☀️ Solaire PV":
        st.title("☀️ Ingénierie Solaire Photovoltaïque")
        nb_p = st.number_input("Nombre de panneaux", min_value=1, value=10)
        p_u = st.number_input("Puissance unitaire (Wp)", value=400)
        st.metric("Puissance Crête Totale", f"{nb_p * p_u / 1000} kWp")

    # ---------------------------------------------------------
    # MODULE 8 : CALCUL DE TERRE
    # ---------------------------------------------------------
    elif menu == "📐 Calcul de Terre":
        st.title("📐 Résistance de la Prise de Terre")
        rho_sol = st.number_input("Résistivité du sol (Ω.m)", value=100)
        st.info("Formule : R = Rho / L (pour un piquet vertical).")

    # --- AUTRES MODULES (PLACEHOLDERS) ---
    else:
        st.title(f"{menu}")
        st.write("Module en cours de développement technique.")

    # --- DÉCONNEXION ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.rerun()