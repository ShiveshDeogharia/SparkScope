# frontend/streamlit_app.py
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import requests
import re

from backend.agents.recommender.rag_query import get_recommendations

from backend.agents.agent_router import get_agent

# -------------------- Session Setup --------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_form" not in st.session_state:
    st.session_state.show_form = False

st.set_page_config(page_title="SparkScope Chat", layout="centered")
st.title("🌱 SparkScope Onboarding Agent")

# -------------------- Replay Chat --------------------
for role, msg in st.session_state.chat_history:
    st.chat_message(role).write(msg)

# -------------------- Chat Input --------------------
user_msg = st.chat_input("Say something like: I used 5000 kWh and shipped 12 pallets over 520 km")

if user_msg:
    st.session_state.chat_history.append(("user", user_msg))

    # Check for recommendation intent
    if any(word in user_msg.lower() for word in ["reduce", "cut", "lower"]):
        for topic in ["electricity", "transport", "packaging"]:
            if topic in user_msg.lower():
                st.session_state.chat_history.append(("assistant", f"💡 Finding ways to reduce **{topic}** emissions..."))
                suggestions = get_agent("recommend")(topic)
                for idea in suggestions:
                    st.session_state.chat_history.append(("assistant", f"• {idea}"))
                st.rerun()
                break  # don't continue if match found

    # Try regex extraction
    electricity_match = re.search(r"(\d+(?:\.\d+)?)\s*kwh", user_msg, re.I)
    freight_match = re.search(r"(\d+)\s*pallets.*?(\d+)\s*km", user_msg, re.I)

    # 👉 Handle recommendation-style queries
    if "reduce" in user_msg.lower() or "cut" in user_msg.lower():
        st.session_state.chat_history.append(("assistant", "🔍 Searching for recommendations..."))
    
        results = get_recommendations(user_msg)

        if results:
            st.session_state.chat_history.append(("assistant", "🎯 Here are some suggestions:"))
            for i, tip in enumerate(results, 1):
                st.session_state.chat_history.append(("assistant", f"{i}. {tip}"))
        else:
            st.session_state.chat_history.append(("assistant", "⚠️ Couldn't find any helpful suggestions. Try rephrasing your question."))

        st.rerun()


    payload = {}
    if electricity_match:
        payload["electricity_kwh"] = float(electricity_match.group(1))
    if freight_match:
        pallets = int(freight_match.group(1))
        km = int(freight_match.group(2))
        payload["road_freight_tkm"] = pallets * km

    if payload:
        st.session_state.chat_history.append(("assistant", f"📦 Extracted activity data:\n```json\n{payload}\n```"))

        # Run verification
        warnings = get_agent("verify")(payload)
        if warnings:
            st.session_state.chat_history.append(("assistant", "🛑 Verification warnings:"))
            for w in warnings:
                st.session_state.chat_history.append(("assistant", f"• {w}"))

        try:
            response = requests.post("http://localhost:8000/api/estimate", json={"activities": payload})
            if response.status_code == 200:
                emissions = response.json()["emissions"]
                st.session_state.chat_history.append(("assistant", f"🌍 Estimated emissions:\n```json\n{emissions}\n```"))
            else:
                st.session_state.chat_history.append(("assistant", f"⚠️ API error: {response.text}"))
        except Exception as e:
            st.session_state.chat_history.append(("assistant", f"❌ Failed to reach API: {e}"))

        st.session_state.show_form = False
        st.rerun()
    else:
        st.session_state.chat_history.append(("assistant", "❌ Sorry, I couldn’t understand the activity data. Please fill the form below."))
        st.session_state.show_form = True
        st.rerun()

# -------------------- Show Fallback Form if Needed --------------------
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

        # Verify payload
        warnings = get_agent("verify")(payload)
        if warnings:
            st.session_state.chat_history.append(("assistant", "🛑 Verification warnings:"))
            for w in warnings:
                st.session_state.chat_history.append(("assistant", f"• {w}"))

        # Estimate emissions
        try:
            response = requests.post("http://localhost:8000/api/estimate", json={"activities": payload})
            if response.status_code == 200:
                emissions = response.json()["emissions"]
                st.session_state.chat_history.append(("assistant", f"🌍 Estimated emissions:\n```json\n{emissions}\n```"))
            else:
                st.session_state.chat_history.append(("assistant", f"⚠️ API error: {response.text}"))
        except Exception as e:
            st.session_state.chat_history.append(("assistant", f"❌ Failed to reach API: {e}"))
        st.session_state.show_form = False
        st.rerun()

# -------------------- Upload PDF Invoice --------------------
st.divider()
st.subheader("📄 Upload an Invoice PDF")

pdf_file = st.file_uploader("Upload your invoice here", type=["pdf"])

if pdf_file is not None:
    # Save uploaded file to a temporary path
    tmp_path = ROOT_DIR / "tmp_invoice.pdf"
    with open(tmp_path, "wb") as f:
        f.write(pdf_file.read())

    # 1. Extract text
    raw_text = get_agent("extract_text")(tmp_path)
    st.text_area("📝 Extracted text:", raw_text, height=200)

    # 2. Extract payload
    payload = get_agent("extract_payload")(raw_text)

    if payload:
        st.success("📦 Extracted activity data:")
        st.code(payload, language="json")

        # 3. Estimate emissions
        emissions = get_agent("estimate_emissions")(payload)
        if emissions:
            st.success("🌍 Estimated emissions from invoice:")
            st.code(emissions, language="json")
        else:
            st.error("⚠️ Failed to estimate emissions. Please try again or enter data manually.")
    else:
        st.warning("⚠️ Couldn’t extract any meaningful activity data from the PDF.")
        st.info("👉 Please use the form above to input your data manually.")


# -------------------- Recommendation Section --------------------
st.divider()
st.subheader("💡 Get Emission Reduction Tips")

reduction_topic = st.selectbox(
    "What type of emission do you want to reduce?",
    ["", "electricity", "transport", "packaging"]
)

if reduction_topic:
    st.info(f"Asking for ideas to reduce: **{reduction_topic}**")
    recommend = get_agent("recommend")
    suggestions = recommend(reduction_topic)

    st.success("Here are some tactics you can try:")
    for idea in suggestions:
        st.markdown(f"• {idea}")
