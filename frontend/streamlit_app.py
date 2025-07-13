# frontend/streamlit_app.py
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import requests
import re
import pandas as pd

from backend.agents.agent_router import get_agent
from backend.agents.recommender.rag_query import get_recommendations

# -------------------- Page Setup --------------------
st.set_page_config(page_title="SparkScope | Emission Assistant", layout="centered")
st.title("🌱 SparkScope — Supplier Sustainability Assistant")
st.markdown("<h4 style='text-align: center; color: grey;'>Helping you estimate, verify, and reduce your carbon footprint.</h4>", unsafe_allow_html=True)

# -------------------- Sidebar Branding --------------------
st.sidebar.image("frontend/assets/spark_walmart_logo.png", use_container_width=True)
st.sidebar.markdown("### SparkScope")
st.sidebar.markdown("Supplier Sustainability Toolkit")
st.sidebar.divider()
st.sidebar.markdown("Built with 💚 for the Walmart Sparkathon")

# -------------------- Utility: Show Dashboard --------------------
def show_dashboard(emissions: dict):
    st.divider()
    st.subheader("📊 Emission Summary")

    st.metric("Total Emissions (kgCO₂e)", f"{emissions['total']:.2f}")

    chart_data = pd.DataFrame({
        "Activity": [k for k in emissions if k != "total"],
        "kgCO2e": [v for k, v in emissions.items() if k != "total"]
    })
    st.bar_chart(chart_data.set_index("Activity"))

    badge = get_agent("badge")(emissions["total"])
    st.success(f"🏅 Supplier Emission Badge: **{badge}**")

# -------------------- Session Setup --------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "emissions" not in st.session_state:
    st.session_state.emissions = None

# -------------------- Chat Agent --------------------
st.divider()
st.subheader("💬 Chat With Our Agent")

user_msg = st.chat_input("Try something like: I used 5000 kWh and shipped 12 pallets over 520 km")

if user_msg:
    st.session_state.chat_history.append(("user", user_msg))

    # 🧠 Trigger Recommendations
    if any(word in user_msg.lower() for word in ["reduce", "cut", "lower"]):
        for topic in ["electricity", "transport", "packaging"]:
            if topic in user_msg.lower():
                st.session_state.chat_history.append(("assistant", f"💡 Finding ways to reduce **{topic}** emissions..."))
                suggestions = get_recommendations(user_msg, topic)
                for idea in suggestions:
                    st.session_state.chat_history.append(("assistant", f"• {idea}"))
                st.rerun()
                break

    # 🧠 Regex-based Extraction
    electricity_match = re.search(r"(\d+(?:\.\d+)?)\s*kwh", user_msg, re.I)
    freight_match = re.search(r"(\d+)\s*pallets.*?(\d+)\s*km", user_msg, re.I)

    payload = {}
    if electricity_match:
        payload["electricity_kwh"] = float(electricity_match.group(1))
    if freight_match:
        pallets = int(freight_match.group(1))
        km = int(freight_match.group(2))
        payload["road_freight_tkm"] = pallets * km

    if payload:
        st.session_state.chat_history.append(("assistant", f"📦 Detected activity data:\n```json\n{payload}\n```"))
        warnings = get_agent("verify")(payload)
        if warnings:
            st.session_state.chat_history.append(("assistant", "⚠️ Verification Warnings:"))
            for w in warnings:
                st.session_state.chat_history.append(("assistant", f"• {w}"))
        try:
            res = requests.post("http://localhost:8000/api/estimate", json={"activities": payload})
            if res.status_code == 200:
                st.session_state.emissions = res.json()["emissions"]
                st.session_state.show_form = False
                st.rerun()
            else:
                st.session_state.chat_history.append(("assistant", f"❌ API Error: {res.text}"))
        except Exception as e:
            st.session_state.chat_history.append(("assistant", f"🚨 API Exception: {e}"))
    else:
        st.session_state.chat_history.append(("assistant", "🔧 I couldn’t understand your data. Please fill the manual form below."))
        st.session_state.show_form = True
        st.rerun()

# -------------------- Replay Chat History --------------------
for role, msg in st.session_state.chat_history:
    st.chat_message(role).write(msg)

# -------------------- Manual Entry Form --------------------
if st.session_state.show_form:
    st.divider()
    with st.expander("📝 Manual Activity Entry", expanded=True):
        with st.form("manual_form"):
            electricity = st.number_input("Electricity (kWh)", min_value=0.0, step=100.0)
            pallets = st.number_input("Pallets shipped", min_value=0)
            distance = st.number_input("Transport distance (km)", min_value=0)
            natural_gas = st.number_input("Natural gas (kWh)", min_value=0.0, step=100.0)
            air_freight = st.number_input("Air freight (tonne-km)", min_value=0.0, step=100.0)
            submitted = st.form_submit_button("Submit Data")

        if submitted:
            payload = {
                "electricity_kwh": electricity,
                "road_freight_tkm": pallets * distance,
                "natural_gas_kwh": natural_gas,
                "air_freight_tkm": air_freight
            }
            st.session_state.chat_history.append(("assistant", f"✅ Received manual data:\n```json\n{payload}\n```"))
            warnings = get_agent("verify")(payload)
            if warnings:
                st.session_state.chat_history.append(("assistant", "⚠️ Verification Warnings:"))
                for w in warnings:
                    st.session_state.chat_history.append(("assistant", f"• {w}"))
            try:
                res = requests.post("http://localhost:8000/api/estimate", json={"activities": payload})
                if res.status_code == 200:
                    st.session_state.emissions = res.json()["emissions"]
                    st.session_state.show_form = False
                    st.rerun()
                else:
                    st.session_state.chat_history.append(("assistant", f"❌ API Error: {res.text}"))
            except Exception as e:
                st.session_state.chat_history.append(("assistant", f"🚨 API Exception: {e}"))

# -------------------- Dashboard --------------------
if st.session_state.emissions:
    show_dashboard(st.session_state.emissions)
    st.session_state.emissions = None

# -------------------- Upload PDF --------------------
st.divider()
with st.expander("📄 Upload Invoice PDF"):
    pdf = st.file_uploader("Upload your invoice (PDF)", type=["pdf"])
    if pdf:
        tmp_path = ROOT_DIR / "tmp_invoice.pdf"
        with open(tmp_path, "wb") as f:
            f.write(pdf.read())

        raw_text = get_agent("extract_text")(tmp_path)
        st.text_area("🧾 Extracted Text", raw_text, height=200)

        payload = get_agent("extract_payload")(raw_text)
        if payload:
            st.success("✅ Activity data extracted:")
            st.code(payload, language="json")

            emissions = get_agent("estimate")(payload)
            if emissions:
                st.session_state.emissions = emissions
                st.rerun()
            else:
                st.error("❌ Emission estimation failed.")
        else:
            st.warning("⚠️ No valid data found.")

# -------------------- Recommendations --------------------
st.divider()
with st.expander("💡 Emission Reduction Tips"):
    reduction_topic = st.selectbox("Choose a category to reduce emissions:", ["", "electricity", "transport", "packaging"])
    if reduction_topic:
        st.info(f"Asking AI for ideas to reduce **{reduction_topic}** emissions...")
        try:
            suggestions = get_recommendations(reduction_topic, reduction_topic)
            if suggestions:
                st.success("Here are your tips:")
                for idea in suggestions:
                    st.markdown(f"• {idea}")
            else:
                st.warning("🤖 AI didn’t return any meaningful tips. Please try again.")
        except Exception as e:
            st.error(f"⚠️ Error while fetching suggestions: {e}")
