import requests
from flask import Blueprint, jsonify
from db_utils import db

bp = Blueprint("customer_location", __name__)

# Indian states mapping (state name -> ISO code)
INDIA_STATES = {
    "Andhra Pradesh": "AP",
    "Arunachal Pradesh": "AR",
    "Assam": "AS",
    "Bihar": "BR",
    "Chhattisgarh": "CT",
    "Goa": "GA",
    "Gujarat": "GJ",
    "Haryana": "HR",
    "Himachal Pradesh": "HP",
    "Jharkhand": "JH",
    "Karnataka": "KA",
    "Kerala": "KL",
    "Madhya Pradesh": "MP",
    "Maharashtra": "MH",
    "Manipur": "MN",
    "Meghalaya": "ML",
    "Mizoram": "MZ",
    "Nagaland": "NL",
    "Odisha": "OD",
    "Punjab": "PB",
    "Rajasthan": "RJ",
    "Sikkim": "SK",
    "Tamil Nadu": "TN",
    "Telangana": "TG",
    "Tripura": "TR",
    "Uttar Pradesh": "UP",
    "Uttarakhand": "UT",
    "West Bengal": "WB",
    "Andaman and Nicobar Islands": "AN",
    "Chandigarh": "CH",
    "Dadra and Nagar Haveli and Daman and Diu": "DD",
    "Delhi": "DL",
    "Jammu and Kashmir": "JK",
    "Ladakh": "LA",
    "Lakshadweep": "LD",
    "Puducherry": "PY",
}

# Reverse mapping (ISO code -> state name)
STATES_BY_CODE = {v: k for k, v in INDIA_STATES.items()}


def _get_api_key():
    """Get CSC API key from site settings"""
    c = db()
    try:
        row = c.execute("SELECT value FROM site_settings WHERE key='site_content'").fetchone()
        if row:
            import json
            content = json.loads(row["value"])
            c.close()
            return content.get("csc_api_key", "")
    except Exception:
        pass
    c.close()
    return ""


@bp.route("/api/location/states", methods=["GET"])
def get_states():
    """Get list of Indian states with codes"""
    states = [{"name": name, "code": code} for name, code in INDIA_STATES.items()]
    return jsonify(states)


@bp.route("/api/location/cities/<state_code>", methods=["GET"])
def get_cities(state_code):
    """Get cities for a given state code using CSC API"""
    api_key = _get_api_key()
    
    if not api_key:
        # Return empty list if no API key configured
        return jsonify([])
    
    try:
        url = f"https://api.countrystatecity.in/v1/countries/IN/states/{state_code}/cities"
        headers = {"X-CSCAPI-KEY": api_key}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            cities = response.json()
            # Return city names sorted alphabetically
            city_names = sorted([city["name"] for city in cities])
            return jsonify(city_names)
        else:
            return jsonify([])
    except Exception as e:
        print(f"Error fetching cities: {e}")
        return jsonify([])
