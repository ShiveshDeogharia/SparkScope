# 🌱 SparkScope — AI-Powered Supplier Onboarding & Emission Reduction Platform

**Built for: Walmart Sparkathon**  
**Goal:** Help suppliers estimate their carbon emissions and receive actionable recommendations to reduce them, accelerating Walmart's Project Gigaton™.

---
## 📽️ Demo Video

[![Watch the demo](https://img.youtube.com/vi/AowVcYrim-c/0.jpg)](https://www.youtube.com/watch?v=AowVcYrim-c)

---

## 🧠 What It Does

SparkScope offers:
- 📄 **Invoice Upload**: Extracts emission activities from PDF invoices.
- 🧠 **Chatbot Input**: Understands natural language like “I used 5000 kWh and shipped 12 pallets over 520 km”.
- ✍️ **Manual Form**: Allows fallback entry for emission data.
- 📊 **Emission Dashboard**: Visualizes total and activity-wise carbon emissions.
- 🏅 **Supplier Badge**: Assigns sustainability badges based on emissions.
- 💡 **RAG Recommendations**: Uses Retrieval-Augmented Generation to suggest emission reduction strategies.

---

## 🗂️ Folder Structure

```
SparkScope/
├── assets/                     # Placeholder for static assets
├── backend/
│   ├── agents/                # All agent logic
│   │   ├── document_ingestion/ -> extract_text.py
│   │   ├── estimator/         -> emission_estimator.py
│   │   ├── recommender/       -> rag_build_index.py, rag_query.py, recommend_actions.py
│   │   ├── verification/      -> badge_logic.py, verify_payload.py
│   │   └── agent_router.py
│   ├── api/                   # FastAPI backend
│   │   └── main.py
│   ├── data/                  # CSV & sample invoice
│   └── faiss_index/           # Vector index for RAG
├── docs/                      # Placeholder for documentation
├── frontend/
│   └── streamlit_app.py       # Main UI
├── hardware/                  # (Future) hardware integration
├── recommender_data/          # RAG source documents
│   ├── electricity_guide.txt
│   ├── packaging_guide.txt
│   └── transport_emissions.txt
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🚀 How to Run Locally

### 1. 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ Make sure Python 3.10+ is installed.

### 2. 🧠 Build the FAISS RAG Index

```bash
python backend/agents/recommender/rag_build_index.py
```

### 3. 🔧 Start the FastAPI Backend

```bash
uvicorn backend.api.main:app --reload
```

### 4. 💻 Run the Streamlit Frontend

```bash
streamlit run frontend/streamlit_app.py
```

---

## 💡 Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI
- **Agents**: Custom logic in Python
- **RAG**: FAISS + HuggingFace + LangChain
- **Extraction**: PDFMiner
- **Verification & Estimation**: DEFRA Carbon Factors Dataset

---

## 🌍 Impact

This tool empowers suppliers with:
- Clarity on their emissions
- Easy onboarding without spreadsheets
- Personalized strategies to cut carbon
- Progress tracking via badges

Together, SparkScope helps Walmart and its suppliers move faster towards Gigaton-scale impact.

---

## 🤝 Team

Built with love by Team Phoenix for the Walmart Sparkathon.  
Let’s decarbonize supply chains, one supplier at a time! 🌎

