# agents/document_ingestion/extract_text.py

from pathlib import Path
import fitz  # PyMuPDF

def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF file using PyMuPDF."""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()

import re

def extract_payload_from_text(text: str) -> dict:
    """
    Extract activity data from invoice-like text.
    Looks for electricity and freight info.
    """
    payload = {}

    elec_match = re.search(r"electricity.*?(\d[\d,\.]*)\s*kwh", text, re.I)
    if elec_match:
        kwh_str = elec_match.group(1).replace(",", "")
        payload["electricity_kwh"] = float(kwh_str)

    freight_match = re.search(r"(\d+)\s*pallets.*?(\d+)\s*km", text, re.I)
    if freight_match:
        pallets = int(freight_match.group(1))
        km = int(freight_match.group(2))
        payload["road_freight_tkm"] = pallets * km

    return payload

import requests

def estimate_emissions_from_payload(payload: dict) -> dict:
    """
    Send the extracted payload to the FastAPI backend and return emissions.
    """
    try:
        response = requests.post("http://localhost:8000/api/estimate", json={"activities": payload})
        if response.status_code == 200:
            return response.json()["emissions"]
        else:
            print("⚠️ API error:", response.text)
            return {}
    except Exception as e:
        print("❌ Failed to reach API:", e)
        return {}


if __name__ == "__main__":
    sample_path = Path(__file__).parent.parent.parent / "data" / "sample_invoice.pdf"
    raw_text = extract_text_from_pdf(sample_path)
    print("📄 Extracted text:\n", raw_text)

    payload = extract_payload_from_text(raw_text)
    print("\n📦 Extracted activity payload:")
    print(payload)

    emissions = estimate_emissions_from_payload(payload)
    print("\n🌍 Estimated emissions:")
    print(emissions)


