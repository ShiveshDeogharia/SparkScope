from pathlib import Path
import pandas as pd

# ---------- Load DEFRA factors once ----------
DATA_DIR = Path(__file__).parent.parent.parent / "data"
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

# Mapping incoming payload keys to (Category, Activity) in the DEFRA table
ACTIVITY_MAP = {
    "electricity_kwh":    ("energy",    "electricity grid average"),
    "road_freight_tkm":   ("transport", "rigid hgv >17t"),
    "natural_gas_kwh":    ("fuel",      "natural gas"),
    "air_freight_tkm":    ("transport", "air freight (intl)")
}





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
    Convert a payload of activities into a dict of emissions.
    Example payload:
        {"electricity_kwh": 5000, "road_freight_tkm": 6240}
    """
    results: dict[str, float] = {}
    total = 0.0

    # ---------- ONE single loop ----------
    for key, amount in payload.items():
        if key not in ACTIVITY_MAP:
            print(f"⚠️  Unknown activity key skipped: {key}")
            continue

        cat, act = ACTIVITY_MAP[key]
        ef = get_factor(cat, act)
        co2 = amount * ef
        results[key] = co2
        total += co2

    results["total"] = total
    return results

if __name__ == "__main__":
    demo_payload = {
        "electricity_kwh": 5000,
        "road_freight_tkm": 12 * 520,
        "natural_gas_kwh": 12000,
        "air_freight_tkm": 2500
    }

    print("🧪 Demo payload →", demo_payload)
    print("🌍 Estimated emissions (kgCO2e):")
    print(estimate_emissions(demo_payload))


