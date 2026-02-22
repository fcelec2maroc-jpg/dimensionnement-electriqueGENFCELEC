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
    menu = st.sidebar.radio("SÉLECTIONNER UN MODULE :", [
        "🔌 Liaison Individuelle",
        "📊 Bilan de Puissance",
        "📉 Correction Cos φ",
        "🚘 Bornes IRVE"
    ])

    # ---------------------------------------------------------
    # MODULE 1 : LIAISON INDIVIDUELLE
    # ---------------------------------------------------------
    if menu == "🔌 Liaison Individuelle":
        st.title("🔌 Dimensionnement de Liaison")
        col_ref1, col_ref2 = st.columns(2)
        nom_projet = col_ref1.text_input("Nom du Projet / Client", "Chantier Client")
        ref_circuit = col_ref2.text_input("Référence du Circuit", "DEPART_01")
        
        st.markdown("---")
        col_in1, col_in2 = st.columns(2)
        with col_in1:
            tension_type = st.radio("Tension", ["Monophasé (230V)", "Triphasé (400V)"])
            nature_cable = st.selectbox("Nature du conducteur", ["Cuivre", "Aluminium"])
            longueur = st.number_input("Longueur du câble (m)", min_value=1, value=50)
        with col_in2:
            mode_saisie = st.radio("Saisie par", ["Puissance (W)", "Courant (A)"])
            if mode_saisie == "Puissance (W)":
                P = st.number_input("Puissance (Watts)", value=3500)
                cos_phi = st.slider("cos φ", 0.7, 1.0, 0.85)
            else:
                Ib_input = st.number_input("Courant Ib (Ampères)", value=16.0)
                cos_phi = 0.85
        
        du_max_pct = st.select_slider("Chute de tension max (%)", options=[3, 5, 8], value=3)

        V = 230 if "Monophasé" in tension_type else 400
        rho = 0.0225 if nature_cable == "Cuivre" else 0.036
        b = 2 if "Monophasé" in tension_type else 1
        Ib = P / (V * cos_phi) if mode_saisie == "Puissance (W)" and b == 2 else P / (V * 1.732 * cos_phi) if mode_saisie == "Puissance (W)" else Ib_input
        
        calibres = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400, 630]
        In = next((x for x in calibres if x >= Ib), calibres[-1])
        S_calc = (b * rho * longueur * Ib) / ((du_max_pct/100)*V)
        sections = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
        S_retenue = next((s for s in sections if s >= S_calc), 240)
        du_pct = ((b * rho * longueur * Ib) / S_retenue / V) * 100

        st.success(f"Section : **{S_retenue} mm²** | Disjoncteur : **{In} A**")

        def generate_pdf_liaison():
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
            for d, v in lignes:
                if "SECTION" in d: pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(255, 140, 0)
                pdf.cell(100, 10, f" {d}", border=1); pdf.cell(90, 10, f" {v}", border=1, ln=True, align="C")
                pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 11)
            return pdf.output()

        if st.button("📄 Télécharger Note de Calcul (PDF)"):
            st.download_button("📥 Télécharger", bytes(generate_pdf_liaison()), f"FCELEC_{ref_circuit}.pdf")

    # ---------------------------------------------------------
    # MODULE 2 : BILAN DE PUISSANCE DÉTAILLÉ (VOTRE DEMANDE)
    # ---------------------------------------------------------
    elif menu == "📊 Bilan de Puissance":
        st.title("📊 Bilan de Puissance Détaillé (Tableau de Répartition)")
        st.markdown("Calculez la puissance totale appelée selon la norme NF C 15-100 en appliquant les coefficients d'utilisation ($K_u$) et de simultanéité ($K_s$).")

        if 'bilan_db' not in st.session_state:
            st.session_state.bilan_db = []

        with st.form("form_add_circuit"):
            st.subheader("➕ Ajouter un nouveau circuit")
            c1, c2, c3 = st.columns([2, 1, 1])
            nom_c = c1.text_input("Désignation (ex: Prises Cuisine)")
            p_inst = c2.number_input("Puissance (W)", min_value=0, value=2000)
            type_c = c3.selectbox("Type de charge", ["Éclairage", "Prises de courant", "Moteur / Pompe", "Chauffage / Clim", "Appareil Cuisson", "Autre"])
            
            # Définition des coefficients Ku par défaut selon la norme
            dict_ku = {"Éclairage": 1.0, "Prises de courant": 0.5, "Moteur / Pompe": 0.8, "Chauffage / Clim": 1.0, "Appareil Cuisson": 0.7, "Autre": 0.8}
            ku_default = dict_ku.get(type_c, 0.8)
            
            ku_choisi = st.slider(f"Coeff d'utilisation (Ku) pour {type_c}", 0.1, 1.0, ku_default)
            
            if st.form_submit_button("Ajouter au tableau"):
                st.session_state.bilan_db.append({
                    "nom": nom_c, "type": type_c, "p_inst": p_inst, "ku": ku_choisi, "p_abs": int(p_inst * ku_choisi)
                })

        if st.session_state.bilan_db:
            st.markdown("### 📋 Tableau Récapitulatif")
            st.table(st.session_state.bilan_db)
            
            total_inst = sum(item['p_inst'] for item in st.session_state.bilan_db)
            total_abs = sum(item['p_abs'] for item in st.session_state.bilan_db)
            
            st.markdown("---")
            st.subheader("📈 Calcul de la Puissance Maximale d'Appel")
            
            # Coefficient de simultanéité selon le nombre de circuits
            nb_c = len(st.session_state.bilan_db)
            ks_default = 1.0 if nb_c <= 1 else 0.9 if nb_c <= 3 else 0.8 if nb_c <= 5 else 0.7
            
            col_ks, col_res = st.columns(2)
            ks_choisi = col_ks.slider("Coeff de Simultanéité Global (Ks)", 0.4, 1.0, ks_default)
            p_finale = int(total_abs * ks_choisi)
            
            with col_res:
                st.metric("Puissance Totale Installée", f"{total_inst} W")
                st.metric("PUISSANCE MAX APPELÉE", f"{p_finale} W", delta=f"Foisonnement : {int(total_inst-p_finale)} W")

            # EXPORT PDF BILAN
            def generate_pdf_bilan():
                pdf = FCELEC_PDF()
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(190, 10, "BILAN DE PUISSANCE DU TABLEAU GENERAL", ln=True, align="C")
                pdf.ln(5)
                # En-têtes tableau
                pdf.set_font("Helvetica", "B", 10); pdf.set_fill_color(220, 220, 220)
                pdf.cell(60, 10, "Désignation", 1, 0, 'C', True)
                pdf.cell(40, 10, "Type", 1, 0, 'C', True)
                pdf.cell(30, 10, "P.Inst (W)", 1, 0, 'C', True)
                pdf.cell(20, 10, "Ku", 1, 0, 'C', True)
                pdf.cell(40, 10, "P.Abs (W)", 1, 1, 'C', True)
                
                pdf.set_font("Helvetica", "", 10)
                for c in st.session_state.bilan_db:
                    pdf.cell(60, 10, c['nom'], 1)
                    pdf.cell(40, 10, c['type'], 1)
                    pdf.cell(30, 10, str(c['p_inst']), 1, 0, 'C')
                    pdf.cell(20, 10, str(c['ku']), 1, 0, 'C')
                    pdf.cell(40, 10, str(c['p_abs']), 1, 1, 'C')
                
                pdf.ln(10)
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(190, 12, f"PUISSANCE TOTALE APPELÉE (Ks = {ks_choisi}) : {p_finale} Watts", border=1, align="C", ln=True)
                return pdf.output()

            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button("📄 Préparer le Rapport Bilan (PDF)"):
                st.download_button("📥 Télécharger le Bilan PDF", bytes(generate_pdf_bilan()), "Bilan_Puissance_FCELEC.pdf")
            if col_btn2.button("🗑️ Vider le Tableau"):
                st.session_state.bilan_db = []; st.rerun()

    # ---------------------------------------------------------
    # MODULE 3 : CORRECTION DU COS PHI
    # ---------------------------------------------------------
    elif menu == "📉 Correction Cos φ":
        st.title("📉 Compensation Énergie Réactive")
        p_kw = st.number_input("Puissance active (kW)", value=100.0)
        c1, c2 = st.columns(2)
        c_ini = c1.slider("Cos φ actuel", 0.4, 0.95, 0.75)
        c_obj = c2.slider("Cos φ visé", 0.9, 1.0, 0.95)
        qc = p_kw * (math.tan(math.acos(c_ini)) - math.tan(math.acos(c_obj)))
        st.success(f"Puissance de la batterie de condensateurs : **{qc:.2f} kVAR**")

    # ---------------------------------------------------------
    # MODULE 4 : BORNES IRVE
    # ---------------------------------------------------------
    elif menu == "🚘 Bornes IRVE":
        st.title("🚘 Mobilité Électrique")
        p_b = st.selectbox("Puissance Borne (kW)", [3.7, 7.4, 11, 22])
        st.info("Protection : Interrupteur différentiel **30mA Type B** impératif.")
        st.warning("Précision : La section minimale du câble doit être de **10 mm²** pour limiter les pertes.")

    # --- LOGOUT ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear(); st.rerun()