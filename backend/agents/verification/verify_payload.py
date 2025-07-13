# backend/agents/verification/verify_payload.py

def verify_payload(payload: dict) -> list[str]:
    """
    Checks for unusual, missing, or suspicious values in the activity payload.
    Returns a list of human-readable warnings.
    """

    warnings = []

    # Define thresholds and descriptions for known inputs
    thresholds = {
        "electricity_kwh": {
            "max": 100_000,
            "label": "Electricity usage (kWh)"
        },
        "road_freight_tkm": {
            "max": 10_000,
            "label": "Freight activity (tonne-kilometres)"
        },
        "natural_gas_kwh": {
            "max": 50_000,
            "label": "Natural gas usage (kWh)"
        },
        "air_freight_tkm": {
            "max": 20_000,
            "label": "Air freight activity (tonne-kilometres)"
        },
    }

    for key, value in payload.items():
        if key not in thresholds:
            continue

        label = thresholds[key]["label"]
        max_val = thresholds[key]["max"]

        if value < 0:
            warnings.append(f"❌ {label} cannot be negative.")
        elif value == 0:
            warnings.append(f"⚠️ {label} is zero — is that intended?")
        elif value > max_val:
            warnings.append(f"⚠️ {label} seems unusually high ({value}).")

    return warnings


# Example test
if __name__ == "__main__":
    test_payload = {
        "electricity_kwh": 250_000,
        "road_freight_tkm": 0,
        "natural_gas_kwh": -100,
        "air_freight_tkm": 30000,
    }

    issues = verify_payload(test_payload)
    print("🚨 Verification results:")
    for w in issues:
        print("-", w)
