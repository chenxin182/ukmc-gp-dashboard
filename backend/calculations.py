import json
import os

_FACTORS_PATH = os.path.join(os.path.dirname(__file__), "factors.json")
with open(_FACTORS_PATH, encoding="utf-8") as _f:
    EMISSION_FACTORS: dict = json.load(_f)


def get_factors() -> dict:
    return EMISSION_FACTORS


def calculate_emissions(company_name: str, country: str, activities: list) -> dict:
    """
    activities: list of objects with .energy_type and .consumption attributes
    Returns a dict with total, scope1, scope2, and per-activity details.
    """
    details = []
    scope1_total = 0.0
    scope2_total = 0.0

    for act in activities:
        energy_type = act.energy_type
        consumption = float(act.consumption)

        if energy_type not in EMISSION_FACTORS:
            raise ValueError(f"Unknown energy type: '{energy_type}'. "
                             f"Valid types: {list(EMISSION_FACTORS.keys())}")

        info = EMISSION_FACTORS[energy_type]
        # Convert kg CO2e/unit → t CO2e/unit
        factor_t = info["factor_kg"] / 1000.0
        emissions = consumption * factor_t
        scope = info["scope"]

        if scope == 1:
            scope1_total += emissions
        else:
            scope2_total += emissions

        details.append({
            "energy_type": energy_type,
            "name": info["name"],
            "consumption": consumption,
            "unit": info["unit"],
            "emission_factor": round(factor_t, 7),
            "emissions": round(emissions, 6),
            "scope": scope,
            "source": info["source"],
        })

    return {
        "company_name": company_name,
        "country": country,
        "total_emissions": round(scope1_total + scope2_total, 4),
        "scope1_emissions": round(scope1_total, 4),
        "scope2_emissions": round(scope2_total, 4),
        "details": details,
    }
