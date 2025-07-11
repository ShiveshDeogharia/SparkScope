# backend/agents/recommender/recommend_actions.py

TACTICS = {
    "electricity": [
        "Switch to renewable energy providers",
        "Install solar panels or on-site generation",
        "Run high-consumption equipment at off-peak hours"
    ],
    "transport": [
        "Use electric delivery vehicles",
        "Consolidate shipments to reduce miles",
        "Switch to rail over road where possible"
    ],
    "packaging": [
        "Use 100% recycled or compostable materials",
        "Minimize box size and filler",
        "Use reusable containers in B2B shipments"
    ]
}

def get_recommendations(topic: str) -> list[str]:
    topic = topic.lower().strip()
    return TACTICS.get(topic, ["No tactics found for that topic. Try 'electricity', 'transport', or 'packaging'."])
