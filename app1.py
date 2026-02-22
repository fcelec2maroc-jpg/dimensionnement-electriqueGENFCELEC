import streamlit as st
import math
from PIL import Image
from fpdf import FPDF

# --- CONFIGURATION ---
st.set_page_config(page_title="FC ELEC - Plateforme Expert", layout="wide")

# --- CLASSE PDF PERSONNALISÉE ---
class FCELEC_PDF(FPDF):
    def header(self):
        try: self.image("logoFCELEC.png", 10, 8, 33)
        except: pass
        self.set_font("Arial", "B", 15)
        self.cell(80)
        self.cell(30, 10, "NOTE DE CALCUL OFFICIELLE", 0, 0, "C")
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "FC ELEC - Contact WhatsApp : +212 6 74 53 42 64 - NF C 15-100", 0, 0, "C")

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
        "🛡️ Sécurité & Lmax",
        "📉 Correction Cos φ",
        "🚘 Bornes IRVE"
    ])

    # ---------------------------------------------------------
    # MODULE 1 : LIAISON INDIVIDUELLE
    # ---------------------------------------------------------
    if menu == "🔌 Liaison Individuelle":
        st.title("🔌 Dimensionnement de Liaison")
        col_ref1, col_ref2 = st.columns(2)
        nom_p = col_ref1.text_input("Projet / Client", "Chantier")
        ref_c = col_ref2.text_input("Référence Circuit", "DEPART_01")

        c1, c2 = st.columns(2)
        with c1:
            tension_type = st.radio("Tension", ["Monophasé (230V)", "Triphasé (400V)"])
            nature_cable = st.selectbox("Conducteur", ["Cuivre", "Aluminium"])
            longueur = st.number_input("Longueur (m)", min_value=1, value=50)
        with c2:
            mode_saisie = st.radio("Saisie par", ["Puissance (W)", "Courant (A)"])
            if mode_saisie == "Puissance (W)":
                P = st.number_input("Puissance (Watts)", value=3500)
                cos_phi = st.slider("cos φ", 0.7, 1.0, 0.85)
            else:
                Ib_input = st.number_input("Courant Ib (Ampères)", value=16.0)
                cos_phi = 0.85
        
        du_max_pct = st.selectbox("Chute de tension max (%)", [3, 5, 8])

        V = 230 if "Monophasé" in tension_type else 400
        rho = 0.0225 if nature_cable == "Cuivre" else 0.036
        b = 2 if "Monophasé" in tension_type else 1
        Ib = P / (V * cos_phi) if mode_saisie == "Puissance (W)" and b == 2 else P / (V * 1.732 * cos_phi) if mode_saisie == "Puissance (W)" else Ib_input
        
        calibres = [10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400, 630]
        In = next((x for x in calibres if x >= Ib), calibres[-1])
        S_calc = (b * rho * longueur * Ib) / ((du_max_pct/100)*V)
        sections = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]
        S_ret = next((s for s in sections if s >= S_calc), sections[-1])
        du_pct = ((b * rho * longueur * Ib) / S_ret / V) * 100

        st.success(f"Résultat : **{S_ret} mm²** | Protection : **{In} A**")

        if st.button("📄 Générer PDF Liaison"):
            pdf = FCELEC_PDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(190, 10, f"PROJET : {nom_p.upper()} - CIRCUIT : {ref_c}", ln=True, border='B')
            pdf.ln(5)
            pdf.set_font("Helvetica", "", 11)
            lignes = [("Tension", tension_type), ("Longueur", f"{longueur} m"), ("Ib", f"{Ib:.2f} A"), ("In", f"{In} A"), ("Chute de tension", f"{du_pct:.2f} %"), ("SECTION RETENUE", f"{S_ret} mm2")]
            for d, v in lignes:
                pdf.cell(100, 10, f" {d}", border=1)
                pdf.cell(90, 10, f" {v}", border=1, ln=True, align="C")
            st.download_button("📥 Télécharger", bytes(pdf.output()), f"Liaison_{ref_c}.pdf")

    # ---------------------------------------------------------
    # MODULE 2 : BILAN DE PUISSANCE DÉTAILLÉ
    # ---------------------------------------------------------
    elif menu == "📊 Bilan de Puissance":
        st.title("📊 Bilan de Puissance Détaillé (Tableau Général)")
        st.write("Calcul des puissances absorbées avec coefficients $K_u$ et $K_s$ par type de charge.")

        if 'bilan_complet' not in st.session_state: st.session_state.bilan_complet = []

        with st.expander("➕ Ajouter un circuit au bilan"):
            col1, col2, col3 = st.columns(3)
            nom = col1.text_input("Désignation du circuit")
            p_inst = col2.number_input("Puissance Installée (W)", value=1000)
            type_c = col3.selectbox("Type de charge", ["Éclairage", "Prises de courant", "Moteur / Pompe", "Chauffage / Clim"])
            
            # Valeurs par défaut NF C 15-100
            default_ku = 1.0 if type_c == "Éclairage" or type_c == "Chauffage / Clim" else 0.8 if type_c == "Moteur / Pompe" else 0.5
            ku = st.slider(f"Coeff d'utilisation (Ku) pour {type_c}", 0.1, 1.0, default_ku)
            
            if st.button("Ajouter au tableau"):
                st.session_state.bilan_complet.append({
                    "nom": nom, "p_inst": p_inst, "type": type_c, "ku": ku, "p_abs": p_inst * ku
                })

        if st.session_state.bilan_complet:
            st.markdown("### Tableau Récapitulatif")
            st.table(st.session_state.bilan_complet)
            
            p_totale_inst = sum(c['p_inst'] for c in st.session_state.bilan_complet)
            p_totale_abs = sum(c['p_abs'] for c in st.session_state.bilan_complet)
            
            st.divider()
            ks = st.slider("Coefficient de Simultanéité Global (Ks)", 0.4, 1.0, 0.7, help="Selon nombre de circuits et foisonnement du tableau.")
            p_appel = p_totale_abs * ks

            c_res1, c_res2 = st.columns(2)
            c_res1.metric("Total Installé", f"{p_totale_inst} W")
            c_res2.metric("Puissance Maximale Appelée (avec Ks)", f"{int(p_appel)} W")

            if st.button("📄 Exporter Bilan en PDF"):
                pdf = FCELEC_PDF()
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(190, 10, "BILAN DE PUISSANCE DU TABLEAU", ln=True, align="C")
                pdf.ln(5)
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(60, 10, "Circuit", 1); pdf.cell(40, 10, "Type", 1); pdf.cell(30, 10, "P.Inst (W)", 1); pdf.cell(20, 10, "Ku", 1); pdf.cell(40, 10, "P.Abs (W)", 1, ln=True)
                pdf.set_font("Helvetica", "", 10)
                for c in st.session_state.bilan_complet:
                    pdf.cell(60, 10, c['nom'], 1); pdf.cell(40, 10, c['type'], 1); pdf.cell(30, 10, str(c['p_inst']), 1); pdf.cell(20, 10, str(c['ku']), 1); pdf.cell(40, 10, str(int(c['p_abs'])), 1, ln=True)
                pdf.ln(10)
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(190, 10, f"PUISSANCE TOTALE APPELÉE (Ks = {ks}) : {int(p_appel)} Watts", border=1, ln=True, align="C")
                st.download_button("📥 Télécharger Bilan PDF", bytes(pdf.output()), "Bilan_Puissance_FCELEC.pdf")

            if st.button("🗑️ Vider le tableau"):
                st.session_state.bilan_complet = []; st.rerun()

    # ---------------------------------------------------------
    # MODULE 3 : SÉCURITÉ & LONGUEUR MAX
    # ---------------------------------------------------------
    elif menu == "🛡️ Sécurité & Longueur Max":
        st.title("🛡️ Sécurité : Longueur Maximale")
        st.info("Vérification du déclenchement magnétique pour la protection des personnes.")
        c1, c2, c3 = st.columns(3)
        s_sec = c1.selectbox("Section (mm²)", [1.5, 2.5, 4, 6, 10, 16])
        cal = c2.number_input("Calibre (A)", value=16)
        courbe = c3.selectbox("Courbe", ["B (5In)", "C (10In)", "D (20In)"])
        m_coef = 5 if "B" in courbe else 10 if "C" in courbe else 20
        l_max = (0.8 * 230 * s_sec) / (0.0225 * 2 * cal * m_coef)
        st.warning(f"La longueur maximale ne doit pas dépasser **{int(l_max)} mètres**.")

    # ---------------------------------------------------------
    # MODULE 4 : CORRECTION DU COS PHI
    # ---------------------------------------------------------
    elif menu == "📉 Correction Cos φ":
        st.title("📉 Compensation Énergie Réactive")
        p_kw = st.number_input("Puissance active de l'installation (kW)", value=50.0)
        c_ini = st.slider("Cos φ actuel", 0.5, 0.95, 0.75)
        c_obj = st.slider("Cos φ visé", 0.9, 1.0, 0.95)
        qc = p_kw * (math.tan(math.acos(c_ini)) - math.tan(math.acos(c_obj)))
        st.success(f"Puissance batterie condensateurs : **{qc:.2f} kVAR**")

    # ---------------------------------------------------------
    # MODULE 5 : BORNES IRVE
    # ---------------------------------------------------------
    elif menu == "🚘 Bornes IRVE":
        st.title("🚘 Infrastructure de Recharge (IRVE)")
        p_borne = st.selectbox("Puissance de la borne (kW)", [3.7, 7.4, 11, 22])
        st.write("Protection préconisée : **Différentiel 30mA Type B**.")
        st.info("Section de câble conseillée : minimum **10 mm²** pour les charges longues.")

    # --- LOGOUT ---
    st.sidebar.markdown("---")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear(); st.rerun()