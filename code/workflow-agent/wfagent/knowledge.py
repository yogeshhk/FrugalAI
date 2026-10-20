"""Small, made-up sample tables that the workflow's tools read. NOT real prices, weather or scheme rules.

They exist so the evaluation can check that the workflow fetches the right row and repeats it faithfully.
Swap in real data by replacing these dictionaries; nothing else changes.
"""

import re
from typing import Dict, List, Optional

NOT_FOUND = "NOT_FOUND"

# (crop, place) -> rupees per quintal
PRICES = {
    ("wheat", "pune"): 2450, ("wheat", "nagpur"): 2380, ("onion", "nashik"): 1850, ("onion", "pune"): 1920,
    ("tomato", "pune"): 1200, ("cotton", "nagpur"): 6900, ("rice", "satara"): 3100, ("soybean", "latur"): 4600,
    ("maize", "solapur"): 2100, ("sugarcane", "kolhapur"): 3150,
}

WEATHER = {
    "pune": {"today": "light rain, 24 C", "tomorrow": "cloudy, 27 C"},
    "nagpur": {"today": "clear, 36 C", "tomorrow": "clear, 37 C"},
    "nashik": {"today": "heavy rain, 22 C", "tomorrow": "showers, 23 C"},
    "latur": {"today": "hot and dry, 38 C", "tomorrow": "hot and dry, 39 C"},
}

SCHEMES = {
    "crop insurance": "Crop insurance: documents needed are the land record, bank passbook and Aadhaar card. "
                      "Last date to apply is 31 July. Apply at your bank or the block office.",
    "loan": "Farm loan scheme: any farmer with a land record can apply at the cooperative bank. "
            "Documents needed are the land record and Aadhaar card. Interest is 4 percent for repayment on time.",
    "drip": "Drip irrigation subsidy: 55 percent of the cost for small farmers. Apply at the agriculture office "
            "with a land record and a quotation from the dealer.",
    "pension": "Farmer pension scheme: open to farmers aged 18 to 40. The monthly payment is 100 rupees. "
               "Enrol at the nearest common service centre.",
}

REPAIR = {
    "tractor": "Tractor that will not start: check fuel, battery terminals and the air filter first. "
               "If it still fails, take it to the nearest service centre.",
    "water pump": "Water pump problem: check the foot valve, the suction pipe for air leaks and the power supply. "
                  "Prime the pump again before restarting.",
    "sprayer": "Sprayer problem: clean the nozzle, check the seals and the pressure valve. Rinse the tank after each use.",
    "tiller": "Tiller problem: check the engine oil, the spark plug and the blade bolts before starting.",
}

# symptom keyword -> advice. Decision support only.
PEST = {
    "yellow": "Yellow spots or leaves can come from a virus, a fungus or lack of nutrients. Remove the worst leaves "
              "and show a leaf to the agriculture officer. This is decision support only.",
    "insect": "Insects on the plants: check the underside of leaves, use a neem oil spray in the evening and ask "
              "the agriculture officer before any chemical. This is decision support only.",
    "worm": "Worms in the crop: pick off visible worms, set pheromone traps and ask the agriculture officer "
            "which spray is safe for this crop. This is decision support only.",
    "powder": "White powder on leaves is usually a fungus: remove infected leaves, keep the leaves dry and ask the "
              "agriculture officer for the right fungicide. This is decision support only.",
    "wilt": "Wilting with rotten roots points to a root rot: improve drainage, stop over-watering and show the "
            "plant to the agriculture officer. This is decision support only.",
}

CROPS = ["wheat", "rice", "onion", "cotton", "soybean", "tomato", "maize", "sugarcane", "saffron", "jowar", "chilli"]
PLACES = ["pune", "nashik", "nagpur", "satara", "latur", "solapur", "kolhapur"]
TOOLS = ["tractor", "water pump", "sprayer", "tiller"]
DAYS = {"today": "today", "tonight": "today", "tomorrow": "tomorrow"}
SCHEME_WORDS = {"insurance": "crop insurance", "loan": "loan", "drip": "drip", "pension": "pension"}
INTENTS = ["weather", "price", "pest", "scheme", "repair", "other"]


def _first(words: List[str], text: str) -> Optional[str]:
    hits = [(text.find(w), w) for w in words if re.search(r"\b" + re.escape(w) + r"\b", text)]
    return min(hits)[1] if hits else None


def extract_slots(message: str) -> Dict[str, Optional[str]]:
    """Plain-code slot filling: look for known words. No model involved, so it costs nothing."""
    t = message.lower()
    day = _first(list(DAYS), t)
    scheme = next((v for k, v in SCHEME_WORDS.items() if k in t), None)
    symptom = next((k for k in PEST if k in t or (k == "insect" and ("bug" in t or "insects" in t))), None)
    return {"crop": _first(CROPS, t), "place": _first(PLACES, t), "tool": _first(TOOLS, t),
            "day": DAYS[day] if day else None, "scheme": scheme, "symptom": symptom}


def numbers_in(text: str) -> List[str]:
    return re.findall(r"\d+(?:\.\d+)?", text)


def rule_intent(message: str) -> str:
    """Keyword fallback classifier. Used when no model is available or the model's answer is unreadable."""
    t = message.lower()
    s = extract_slots(message)
    if re.search(r"\b(rain|weather|forecast|storm|temperature|hot|sky|wind|showers)\b", t):
        return "weather"
    if re.search(r"\b(price|rate|selling|sell|fetch|cost|mandi|market)\b", t) or "how much is" in t:
        return "price"
    if s["tool"]:
        return "repair"
    if s["scheme"] or re.search(r"\b(subsidy|scheme|eligible|apply|form)\b", t):
        return "scheme"
    if re.search(r"\b(repair|engine|start|serviced|fix|noise|machine|harvester|thresher|pump)\b", t):
        return "repair"
    if s["symptom"] or re.search(r"\b(disease|leaves|spots|rotting|attacking|worms?|insects?|bugs?)\b", t):
        return "pest"
    return "other"
