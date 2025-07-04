from pathlib import Path
import pandas as pd

# ---------- Load DEFRA factors once ----------
DATA_DIR = Path(__file__).parent.parent / "data"
DEFRA_CSV = DATA_DIR / "defra_factors.csv"

def _load_factors() -> pd.DataFrame:
    """Read the factors CSV into memory (runs only at first import)."""
    df = pd.read_csv(DEFRA_CSV)
    # Normalise strings for easier matching
    return df.assign(
        Category=df["Category"].str.lower(),
        Activity=df["Activity"].str.lower()
    )

FACTORS = _load_factors()


def get_factor(category: str, activity: str) -> float:
    """
    Return kgCO₂e per unit for a given category + activity.
    Strings are matched case‑insensitively.
    """
    cat = category.lower()
    act = activity.lower()
    row = FACTORS.query("Category == @cat and Activity == @act")
    if row.empty:
        raise KeyError(f"Emission factor not found for {category} / {activity}")
    return float(row["kgCO2e_per_unit"].iloc[0])



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
    demo_payload = {
    "electricity_kwh": 5000,          # 5 MWh electricity
    "road_freight_tkm": 12 * 520      # 12 pallets × 520 km
}
print("Demo payload →", demo_payload)
print("Estimated emissions (kgCO2e):")
print(estimate_emissions(demo_payload))


