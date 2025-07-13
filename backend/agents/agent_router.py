# backend/agents/agent_router.py

from .verification.verify_payload import verify_payload
from .recommender.rag_query import get_recommendations
from .document_ingestion.extract_text import (
    extract_text_from_pdf,
    extract_payload_from_text,
    estimate_emissions_from_payload,
)
from .verification.badge_logic import get_supplier_badge

# Central agent registry
AGENTS = {
    "verify": verify_payload,
    "recommend": get_recommendations,
    "extract_text": extract_text_from_pdf,
    "extract_payload": extract_payload_from_text,
    "estimate": estimate_emissions_from_payload,
    "badge": get_supplier_badge,
}


def get_agent(name: str):
    """
    Retrieves the callable agent function by name.

    Args:
        name (str): Agent key, e.g. 'verify', 'recommend'

    Returns:
        Callable agent function.

    Raises:
        ValueError: If the agent name is not in the registry.
    """
    agent = AGENTS.get(name)
    if not agent:
        raise ValueError(f"❌ Agent '{name}' not found. Available agents: {list(AGENTS.keys())}")
    return agent
