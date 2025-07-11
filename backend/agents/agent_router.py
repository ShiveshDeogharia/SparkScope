# backend/agents/agent_router.py

from .verification.verify_payload import verify_payload
from .document_ingestion.extract_text import (
    extract_text_from_pdf,
    extract_payload_from_text,
    estimate_emissions_from_payload
)
from .recommender.recommend_actions import get_recommendations

# Central registry of all callable agents
AGENT_REGISTRY = {
    "verify": verify_payload,
    "extract_text": extract_text_from_pdf,
    "extract_payload": extract_payload_from_text,
    "estimate_emissions": estimate_emissions_from_payload,
    "recommend": get_recommendations
}

def get_agent(name):
    """Return the function associated with the agent name."""
    agent = AGENT_REGISTRY.get(name)
    if not agent:
        raise ValueError(f"No agent found for: '{name}'")
    return agent
