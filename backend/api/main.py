# backend/api/main.py
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

# Import your estimator
from backend.agents.estimator.emission_estimator import estimate_emissions

app = FastAPI(title="SparkScope API", version="0.1")

# Define the expected request schema
class EmissionPayload(BaseModel):
    activities: Dict[str, float]  # example: {"electricity_kwh": 5000, "road_freight_tkm": 6240}

# Define the root route
@app.get("/")
def root():
    return {"message": "SparkScope API is alive 🚀"}

# Define the emissions endpoint
@app.post("/api/estimate")
def estimate(payload: EmissionPayload):
    try:
        results = estimate_emissions(payload.activities)
        return {"status": "success", "emissions": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
