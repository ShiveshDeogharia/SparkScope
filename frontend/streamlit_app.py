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

# -------------------- Utility --------------------
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
    st.success(f"🏍️ Supplier Badge: **{badge}**")

# -------------------- Session Setup --------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_form" not in st.session_state:
    st.session_state.show_form = False
if "emissions" not in st.session_state:
    st.session_state.emissions = None

st.set_page_config(page_title="SparkScope Chat", layout="centered")
st.title("🌱 SparkScope Onboarding Agent")

# -------------------- Replay Chat History --------------------
for role, msg in st.session_state.chat_history:
    st.chat_message(role).write(msg)

# -------------------- Chat Input --------------------
user_msg = st.chat_input("Say something like: I used 5000 kWh and shipped 12 pallets over 520 km")

if user_msg:
    st.session_state.chat_history.append(("user", user_msg))

    # 🔍 Recommendation Queries
    if any(word in user_msg.lower() for word in ["reduce", "cut", "lower"]):
        for topic in ["electricity", "transport", "packaging"]:
            if topic in user_msg.lower():
                st.session_state.chat_history.append(("assistant", f"💡 Finding ways to reduce **{topic}** emissions..."))
                suggestions = get_recommendations(user_msg, topic)
                for idea in suggestions:
                    st.session_state.chat_history.append(("assistant", f"• {idea}"))
                st.rerun()
                break

    # 🧐 Regex Extraction
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
        st.session_state.chat_history.append(("assistant", f"📦 Extracted activity data:\n```json\n{payload}\n```"))

        warnings = get_agent("verify")(payload)
        if warnings:
            st.session_state.chat_history.append(("assistant", "🛑 Verification warnings:"))
            for w in warnings:
                st.session_state.chat_history.append(("assistant", f"• {w}"))

        try:
            response = requests.post("http://localhost:8000/api/estimate", json={"activities": payload})
            if response.status_code == 200:
                st.session_state.emissions = response.json()["emissions"]
                st.session_state.show_form = False
                st.rerun()
            else:
                st.session_state.chat_history.append(("assistant", f"⚠️ API error: {response.text}"))
        except Exception as e:
            st.session_state.chat_history.append(("assistant", f"❌ Failed to reach API: {e}"))
    else:
        st.session_state.chat_history.append(("assistant", "❌ Sorry, I couldn’t understand the activity data. Please fill the form below."))
        st.session_state.show_form = True
        st.rerun()

# -------------------- Fallback Manual Form --------------------
if st.session_state.show_form:
    with st.form("fallback_form"):
        st.write("👉 Please enter your activity data manually:")

        electricity = st.number_input("Electricity used (kWh)", min_value=0.0, step=100.0)
        pallets = st.number_input("Road freight: Number of pallets", min_value=0, step=1)
        distance = st.number_input("Road freight: Distance transported (km)", min_value=0, step=10)
        natural_gas = st.number_input("Natural gas used (kWh)", min_value=0.0, step=100.0)
        air_freight = st.number_input("Air freight (tonne-km)", min_value=0.0, step=100.0)

        submitted = st.form_submit_button("Submit")

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
            st.session_state.chat_history.append(("assistant", "🛑 Verification warnings:"))
            for w in warnings:
                st.session_state.chat_history.append(("assistant", f"• {w}"))

        try:
            response = requests.post("http://localhost:8000/api/estimate", json={"activities": payload})
            if response.status_code == 200:
                st.session_state.emissions = response.json()["emissions"]
                st.session_state.show_form = False
                st.rerun()
            else:
                st.session_state.chat_history.append(("assistant", f"⚠️ API error: {response.text}"))
        except Exception as e:
            st.session_state.chat_history.append(("assistant", f"❌ Failed to reach API: {e}"))

# -------------------- Show Dashboard --------------------
if st.session_state.emissions:
    show_dashboard(st.session_state.emissions)
    st.session_state.emissions = None

# -------------------- Upload PDF Invoice --------------------
st.divider()
st.subheader("📄 Upload an Invoice PDF")

pdf_file = st.file_uploader("Upload your invoice here", type=["pdf"])

if pdf_file is not None:
    tmp_path = ROOT_DIR / "tmp_invoice.pdf"
    with open(tmp_path, "wb") as f:
        f.write(pdf_file.read())

    raw_text = get_agent("extract_text")(tmp_path)
    st.text_area("📝 Extracted text:", raw_text, height=200)

    payload = get_agent("extract_payload")(raw_text)

    if payload:
        st.success("📦 Extracted activity data:")
        st.code(payload, language="json")

        emissions = get_agent("estimate")(payload)
        if emissions:
            st.session_state.emissions = emissions
            st.rerun()
        else:
            st.error("⚠️ Failed to estimate emissions. Please try again or enter data manually.")
    else:
        st.warning("⚠️ Couldn’t extract any activity data.")
        st.info("👉 Try re-uploading or use the form above.")

# -------------------- Emission Reduction Tips --------------------
st.divider()
st.subheader("💡 Get Emission Reduction Tips")

reduction_topic = st.selectbox(
    "What type of emission do you want to reduce?",
    ["", "electricity", "transport", "packaging"]
)

if reduction_topic:
    st.info(f"Asking for ideas to reduce: **{reduction_topic}**")
    suggestions = get_recommendations(user_msg or reduction_topic, reduction_topic)


    st.success("Here are some tactics you can try:")
    for idea in suggestions:
        st.markdown(f"• {idea}")
