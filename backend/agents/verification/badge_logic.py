# backend/agents/verification/badge_logic.py

def get_supplier_badge(total_emissions: float) -> str:
    if total_emissions > 1000:
        return "🟤 Bronze"
    elif total_emissions > 500:
        return "🥈 Silver"
    else:
        return "🥇 Gold"
