# frontend/streamlit_app.py
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


import streamlit as st
import requests
import re

from backend.agents.verification.verify_payload import verify_payload



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

    # Try regex extraction
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
        # 1. Show the extracted payload
        st.session_state.chat_history.append(("assistant", f"📦 Extracted activity data:\n```json\n{payload}\n```"))

        # 2. Run verification
        warnings = verify_payload(payload)
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
        pallets = st.number_input("Number of pallets", min_value=0, step=1)
        distance = st.number_input("Distance transported (km)", min_value=0, step=10)
        submitted = st.form_submit_button("Submit")

    if submitted:
        payload = {
            "electricity_kwh": electricity,
            "road_freight_tkm": pallets * distance
        }
        st.session_state.chat_history.append(("assistant", f"✅ Received manual data:\n```json\n{payload}\n```"))

# 🛡️ Verify the payload here too
        warnings = verify_payload(payload)
        if warnings:
            st.session_state.chat_history.append(("assistant", "🛑 Verification warnings:"))
            for w in warnings:
                st.session_state.chat_history.append(("assistant", f"• {w}"))

# 🌍 Call the backend
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
    from backend.agents.document_ingestion.extract_text import (
        extract_text_from_pdf,
        extract_payload_from_text,
        estimate_emissions_from_payload
    )

    # Save uploaded file to a temporary path
    tmp_path = ROOT_DIR / "tmp_invoice.pdf"
    with open(tmp_path, "wb") as f:
        f.write(pdf_file.read())

    # 1. Extract text
    raw_text = extract_text_from_pdf(tmp_path)
    st.text_area("📝 Extracted text:", raw_text, height=200)

    # 2. Extract payload
    payload = extract_payload_from_text(raw_text)

    if payload:
        st.success("📦 Extracted activity data:")
        st.code(payload, language="json")

        # 3. Estimate emissions
        emissions = estimate_emissions_from_payload(payload)
        if emissions:
            st.success("🌍 Estimated emissions from invoice:")
            st.code(emissions, language="json")
        else:
            st.error("⚠️ Failed to estimate emissions. Please try again or enter data manually.")
    else:
        st.warning("⚠️ Couldn’t extract any meaningful activity data from the PDF.")
        st.info("👉 Please use the form above to input your data manually.")
