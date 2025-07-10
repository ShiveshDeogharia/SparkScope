# agents/verification/verify_payload.py

def verify_payload(payload: dict) -> list[str]:
    """
    Check for outliers or suspicious values in the activity payload.
    Returns a list of warning strings.
    """

    warnings = []

    # Thresholds for expected ranges (can be learned over time)
    thresholds = {
        "electricity_kwh": {"max": 100_000, "label": "Electricity usage"},
        "road_freight_tkm": {"max": 10_000, "label": "Freight distance × pallets"},
    }

    for key, value in payload.items():
        if key not in thresholds:
            continue
        if value < 0:
            warnings.append(f"❌ {thresholds[key]['label']} cannot be negative.")
        elif value == 0:
            warnings.append(f"⚠️ {thresholds[key]['label']} is zero — is that correct?")
        elif value > thresholds[key]["max"]:
            warnings.append(f"⚠️ {thresholds[key]['label']} seems unusually high ({value}).")

    return warnings

if __name__ == "__main__":
    test_payload = {
        "electricity_kwh": 250_000,
        "road_freight_tkm": 0
    }

    issues = verify_payload(test_payload)
    print("🚨 Verification results:")
    for w in issues:
        print("-", w)
