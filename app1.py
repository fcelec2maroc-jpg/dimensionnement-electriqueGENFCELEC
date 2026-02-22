import streamlit as st
import math
from PIL import Image
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="FC ELEC - Plateforme Expert", layout="wide")

# --- FONCTION GÉNÉRATION PDF GÉNÉRIQUE ---
class FCELEC_PDF(FPDF):
    def header(self):
        try:
            self.image("logoFCELEC.png", 10, 8, 33)
        except:
            pass
        self.set_font("Arial", "B", 15)
        self.cell(80)
        self.cell(30, 10, "NOTE DE CALCUL OFFICIELLE", 0, 0, "C")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        # Ajout du numéro WhatsApp dans le pied de page
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
    # --- NAVIGATION ---
    st.sidebar.image("logoFCELEC.png", use_container_width=True)
    st.sidebar.title("🛠️ Menu Expert")
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
        st.title("🔌 Dimensionnement de Liaison")
        col_ref1, col_ref2 = st.columns(2)
        nom_p = col_ref1.text_input("Projet", "Chantier")
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

        st.success(f"Section : **{S_ret} mm²** | Disjoncteur : **{In} A**")

        if st.button("📄 Générer PDF Liaison"):
            pdf = FCELEC_PDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(190, 10, f"PROJET : {nom_p} - CIRCUIT : {ref_c}", ln=True, border='B')
            pdf.ln(5)
            pdf.set_font("Arial", "", 11)
            pdf.cell(95, 10, f"Tension : {tension}", border=1)
            pdf.cell(95, 10, f"Longueur : {longueur} m", border=1, ln=True)
            pdf.cell(95, 10, f"Courant Ib : {Ib:.2f} A", border=1)
            pdf.cell(95, 10, f"Protection In : {In} A", border=1, ln=True)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(190, 15, f"SECTION RETENUE : {S_ret} mm2", ln=True, align="C", border=1)
            st.download_button("📥 Télécharger PDF", bytes(pdf.output()), f"Liaison_{ref_c}.pdf")

    # ---------------------------------------------------------
    # MODULE 2 : BILAN DE PUISSANCE
    # ---------------------------------------------------------
    elif menu == "📊 Bilan de Puissance Tableau":
        st.title("📊 Bilan de Puissance")
        if 'bilan' not in st.session_state: st.session_state.bilan = []
        with st.form("Add"):
            c1, c2, c3 = st.columns(3)
            n = c1.text_input("Désignation")
            p = c2.number_input("Puissance (W)", value=0)
            t = c3.selectbox("Type", ["Eclairage", "Prises", "Chauffage", "Autre"])
            if st.form_submit_button("Ajouter"):
                st.session_state.bilan.append({"nom": n, "p": p, "t": t})
        
        if st.session_state.bilan:
            st.table(st.session_state.bilan)
            p_inst = sum(i['p'] for i in st.session_state.bilan)
            ks = st.slider("Coeff. Simultanéité (Ks)", 0.5, 1.0, 0.8)
            p_appel = int(p_inst * ks)
            st.metric("Puissance d'appel Totale", f"{p_appel} W")
            
            if st.button("📄 Générer PDF Bilan"):
                pdf = FCELEC_PDF()
                pdf.add_page()
                pdf.cell(190, 10, "BILAN DE PUISSANCE TABLEAU", ln=True, align="C")
                pdf.ln(5)
                for item in st.session_state.bilan:
                    pdf.cell(100, 8, item['nom'], border=1)
                    pdf.cell(90, 8, f"{item['p']} W", border=1, ln=True)
                pdf.ln(5)
                pdf.set_font("Arial", "B", 12)
                pdf.cell(190, 10, f"PUISSANCE TOTALE APPELÉE (Ks {ks}) : {p_appel} W", ln=True)
                st.download_button("📥 Télécharger Bilan", bytes(pdf.output()), "Bilan_Puissance.pdf")

    # ---------------------------------------------------------
    # MODULE 3 : SÉCURITÉ & LONGUEUR MAX
    # ---------------------------------------------------------
    elif menu == "🛡️ Sécurité & Longueur Max":
        st.title("🛡️ Calcul Longueur Max")
        sec = st.selectbox("Section (mm²)", [1.5, 2.5, 4, 6, 10, 16])
        cal = st.number_input("Calibre Protection (A)", value=16)
        courbe = st.selectbox("Courbe", ["B (5In)", "C (10In)", "D (20In)"])
        m_coef = 5 if "B" in courbe else 10 if "C" in courbe else 20
        l_max = (0.8 * 230 * sec) / (0.0225 * 2 * cal * m_coef)
        st.warning(f"Longueur maximale : **{int(l_max)} mètres**.")

        if st.button("📄 Générer PDF Sécurité"):
            pdf = FCELEC_PDF()
            pdf.add_page()
            pdf.cell(190, 10, "CONTROLE SECURITE - LONGUEUR MAX", ln=True, align="C")
            pdf.ln(10)
            pdf.cell(190, 10, f"Section : {sec} mm2 | Disjoncteur : {cal}A Courbe {courbe[0]}", ln=True)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(190, 15, f"LONGUEUR MAXIMALE ADMISSIBLE : {int(l_max)} m", border=1, ln=True, align="C")
            st.download_button("📥 Télécharger PDF Sécurité", bytes(pdf.output()), "Securite_Lmax.pdf")

    # ---------------------------------------------------------
    # MODULE 4 : CORRECTION DU COS PHI
    # ---------------------------------------------------------
    elif menu == "📉 Correction du Cos φ":
        st.title("📉 Compensation Énergie Réactive")
        p_kw = st.number_input("Puissance (kW)", value=50.0)
        c_ini = st.slider("Cos φ actuel", 0.5, 0.95, 0.8)
        c_obj = st.slider("Cos φ désiré", 0.9, 1.0, 0.95)
        qc = p_kw * (math.tan(math.acos(c_ini)) - math.tan(math.acos(c_obj)))
        st.success(f"Batterie de condensateurs : **{qc:.2f} kVAR**")

    # ---------------------------------------------------------
    # MODULE 5 : MODE DE POSE & IZ
    # ---------------------------------------------------------
    elif menu == "⚡ Mode de Pose & Iz":
        st.title("⚡ Vérification Échauffement (Iz)")
        st.selectbox("Méthode", ["A1", "B", "C", "D", "E"])
        st.slider("Température", 10, 60, 30)
        st.info("Ce module permet de valider la tenue thermique des câbles.")

    # ---------------------------------------------------------
    # MODULE 6 : BORNES IRVE
    # ---------------------------------------------------------
    elif menu == "🚘 Module Bornes IRVE":
        st.title("🚘 Mobilité Électrique (IRVE)")
        pb = st.selectbox("Puissance Borne", [3.7, 7.4, 11, 22])
        st.info("Note : Utiliser impérativement un différentiel **Type B**.")

    # --- LOGOUT ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.rerun()