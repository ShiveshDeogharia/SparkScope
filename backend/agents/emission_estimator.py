import pandas as pd

# load DEFRA factors once
DEFRA = pd.read_csv("../data/defra_factors.csv")  # adjust path if needed

def get_factor(category: str, activity: str) -> float:
    """Return kgCO₂e per unit for a given activity (very rough MVP)."""
    row = DEFRA.query("Category == @category and Activity == @activity")
    if row.empty:
        raise ValueError("EF not found, fallback needed")
    return row["kgCO2e_per_unit"].iloc[0]

def estimate_emissions(payload: dict) -> dict:
    """
    payload example:
    {
        "electricity_kwh": 5000,
        "road_freight_tkm": 12 * 520  # pallets × km
    }
    """
    results = {}
    total = 0.0

    if "electricity_kwh" in payload:
        ef = get_factor("Energy", "Electricity grid average")
        co2 = payload["electricity_kwh"] * ef
        results["electricity"] = co2
        total += co2

    if "road_freight_tkm" in payload:
        ef = get_factor("Transport", "Rigid HGV >17t")
        co2 = payload["road_freight_tkm"] * ef
        results["transport"] = co2
        total += co2

    results["total"] = total
    return results

if __name__ == "__main__":
    demo = {"electricity_kwh": 5000, "road_freight_tkm": 12 * 520}
    print(estimate_emissions(demo))
