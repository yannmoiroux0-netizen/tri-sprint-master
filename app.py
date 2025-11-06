import streamlit as st
from datetime import date
from core.models import AthleteProfile
from core.zones import zones_summary, pace_from_vma, swim_pace_from_css, bike_w_from_ftp
from core.plan_engine import build_week
from core.scheduler import apply_guardrails, apply_imprevu
from core.exports import to_csv, to_markdown, to_ics
import pandas as pd

st.set_page_config(page_title="Tri Sprint Master V10 — Perfect", layout="wide")
st.title("Tri Sprint Master V10 — Perfect")
st.caption("Wizard de semaine, imprevus intelligents, garde-fous, exports, CLI/Docker.")

with st.sidebar:
    st.header("Wizard: Profil & Etat")
    step = st.radio("Etapes", ["Profil", "Etat du jour", "Date cible"])

    if "profile" not in st.session_state:
        st.session_state["profile"] = {
            "name":"Yann","weight":71.0,"ftp":227,"vma":18.5,"css":110,"hr_max":195,"hr_rest":50
        }
    if step=="Profil":
        st.session_state["profile"]["name"] = st.text_input("Nom", st.session_state["profile"]["name"])
        st.session_state["profile"]["weight"] = st.number_input("Poids (kg)", 50.0, 120.0, st.session_state["profile"]["weight"], step=0.5)
        st.session_state["profile"]["ftp"] = st.number_input("FTP (W)", 100, 450, st.session_state["profile"]["ftp"], step=1)
        st.session_state["profile"]["vma"] = st.number_input("VMA (km/h)", 12.0, 24.0, st.session_state["profile"]["vma"], step=0.1)
        st.session_state["profile"]["css"] = st.number_input("CSS (sec/100m)", 60, 140, st.session_state["profile"]["css"], step=1)
        st.session_state["profile"]["hr_max"] = st.number_input("FC Max", 140, 210, st.session_state["profile"]["hr_max"], step=1)
        st.session_state["profile"]["hr_rest"] = st.number_input("FC Repos", 35, 80, st.session_state["profile"]["hr_rest"], step=1)
    elif step=="Etat du jour":
        st.session_state["sleep_h"] = st.slider("Sommeil (h)", 3.0, 10.0, 7.0, 0.5)
        st.session_state["soreness"] = st.slider("Courbatures (1-10)", 1, 10, 4)
        st.session_state["stress"] = st.slider("Stress (1-10)", 1, 10, 4)
        st.session_state["fatigue"] = st.slider("Fatigue percue (1-10)", 1, 10, 5)
    elif step=="Date cible":
        st.session_state["target_date"] = st.date_input("Date de reference", date.today())

profile = st.session_state.get("profile")
ap = AthleteProfile(name=profile["name"], weight_kg=profile["weight"], ftp_w=int(profile["ftp"]),
                    vma_kmh=float(profile["vma"]), css_s_per_100=int(profile["css"]),
                    hr_max=int(profile["hr_max"]), hr_rest=int(profile["hr_rest"]))

st.subheader("Zones personnalisees")
zones = zones_summary(ap.ftp_w, ap.vma_kmh, ap.css_s_per_100, ap.hr_rest, ap.hr_max)
st.dataframe(pd.DataFrame(zones).T)

st.markdown("---")
st.header("Semaine generee")
target_date = st.session_state.get("target_date", date.today())
fatigue = int(st.session_state.get("fatigue", 5))

wk = build_week(target_date)
wk_guard = apply_guardrails(wk, fatigue_score=fatigue)

col1, col2 = st.columns(2)
with col1:
    st.write(f"Semaine du {wk_guard.start_date.strftime('%d %b %Y')} — {wk_guard.label} [{wk_guard.block}]")
    st.write(f"TSS estime: {wk_guard.tss()} (cible {wk_guard.target_tss}) — Volume cible: {wk_guard.target_volume_h} h")
    df = pd.DataFrame(wk_guard.as_dataframe())
    st.dataframe(df, use_container_width=True)

with col2:
    st.subheader("Imprevus")
    day = st.selectbox("Jour impacte", ["Aucun"]+["LUN","MAR","MER","JEU","VEN","SAM","DIM"])
    banned = st.multiselect("Sports indisponibles", ["Renfo","Nat","Velo","CàP","Mobilite"])
    if st.button("Replanifier intelligemment", use_container_width=True):
        if day == "Aucun" or not banned:
            st.info("Choisis un jour et au moins un sport a deplacer.")
        else:
            wk_adj = apply_imprevu(wk_guard, day, banned_sports=banned)
            st.session_state["wk_adj"] = wk_adj
            st.success("Replanification effectuee.")
    if "wk_adj" in st.session_state:
        st.write(f"Plan ajuste — TSS estime: {st.session_state['wk_adj'].tss()}")
        st.dataframe(pd.DataFrame(st.session_state["wk_adj"].as_dataframe()), use_container_width=True)

st.markdown("---")
st.header("Exports")
c1, c2, c3 = st.columns(3)
with c1:
    st.download_button("CSV", to_csv(wk_guard), "semaine.csv", "text/csv")
with c2:
    st.download_button("ICS", to_ics(wk_guard), "semaine.ics", "text/calendar")
with c3:
    st.download_button("Markdown", to_markdown(wk_guard), "semaine.md", "text/markdown")

st.markdown("---")
with st.expander("Details allures"):
    st.markdown(f"- Bike @ FTP: {ap.ftp_w} W | 95% -> {int(round(ap.ftp_w*0.95))} W | 105% -> {int(round(ap.ftp_w*1.05))} W")
    st.markdown(f"- Run @ AS10 (90-95% VMA): {pace_from_vma(ap.vma_kmh,0.90)} a {pace_from_vma(ap.vma_kmh,0.95)}")
    st.markdown(f"- Run @ Sprint (95-102% VMA): {pace_from_vma(ap.vma_kmh,0.95)} a {pace_from_vma(ap.vma_kmh,1.02)}")
    st.markdown(f"- Swim @ CSS: {ap.css_s_per_100//60}:{ap.css_s_per_100%60:02d}/100m | +6s -> {swim_pace_from_css(ap.css_s_per_100,6)}")
