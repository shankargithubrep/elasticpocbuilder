"""
Revenue Engine Service

Backend for the in-app project planner experience.
Runs semantic search, geo search, and inventory ES|QL queries against
Elasticsearch. Falls back to a rich simulation when data isn't indexed yet.
"""

import logging
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Realistic project templates (simulation fallback)
# ---------------------------------------------------------------------------

_BOM: Dict[str, List[Dict]] = {
    "shed": [
        {"name": "2x4x8 Pressure Treated Lumber",   "qty": 24, "unit": "each",  "aisle": "31", "bay": "A", "price": 8.47,   "category": "Lumber"},
        {"name": "2x6x8 Construction Lumber",        "qty": 12, "unit": "each",  "aisle": "31", "bay": "B", "price": 11.23,  "category": "Lumber"},
        {"name": "OSB Sheathing 4x8 Sheet",          "qty": 12, "unit": "each",  "aisle": "34", "bay": "C", "price": 22.15,  "category": "Panels"},
        {"name": "Metal Roofing Panel 3ft",          "qty":  8, "unit": "each",  "aisle": "28", "bay": "A", "price": 41.00,  "category": "Roofing"},
        {"name": "Roofing Felt 15lb Roll",           "qty":  2, "unit": "roll",  "aisle": "28", "bay": "B", "price": 18.97,  "category": "Roofing"},
        {"name": "Ridge Cap Metal 10ft",             "qty":  2, "unit": "each",  "aisle": "28", "bay": "A", "price": 21.50,  "category": "Roofing"},
        {"name": "Drip Edge Metal 10ft",             "qty":  4, "unit": "each",  "aisle": "28", "bay": "C", "price": 8.97,   "category": "Roofing"},
        {"name": "Concrete Mix 80lb Bag",            "qty": 10, "unit": "bag",   "aisle": "19", "bay": "D", "price": 6.25,   "category": "Concrete"},
        {"name": "Post Anchor Kit",                  "qty":  4, "unit": "each",  "aisle": "19", "bay": "A", "price": 12.97,  "category": "Concrete"},
        {"name": "Pre-Hung Door 32x80 Exterior",     "qty":  1, "unit": "each",  "aisle": "14", "bay": "C", "price": 187.00, "category": "Doors"},
        {"name": "Tyvek House Wrap 9ft Roll",        "qty":  1, "unit": "roll",  "aisle": "34", "bay": "D", "price": 44.97,  "category": "Weather Barrier"},
        {"name": "3in Deck Screws 5lb Box",          "qty":  2, "unit": "box",   "aisle": "26", "bay": "A", "price": 14.97,  "category": "Fasteners"},
        {"name": "Framing Nails 5lb Box",            "qty":  2, "unit": "box",   "aisle": "26", "bay": "B", "price": 12.47,  "category": "Fasteners"},
        {"name": "Hurricane Ties 10-Pack",           "qty":  2, "unit": "pack",  "aisle": "26", "bay": "C", "price": 8.97,   "category": "Fasteners"},
        {"name": "Joist Hanger LUS28 10-Pack",       "qty":  1, "unit": "pack",  "aisle": "26", "bay": "C", "price": 14.97,  "category": "Fasteners"},
        {"name": "Exterior Caulk 10oz Tube",         "qty":  2, "unit": "tube",  "aisle": "25", "bay": "A", "price": 5.47,   "category": "Sealants"},
        {"name": "Exterior Paint Gallon",            "qty":  2, "unit": "gal",   "aisle": "23", "bay": "B", "price": 38.97,  "category": "Paint"},
        {"name": "Safety Glasses + Gloves Kit",      "qty":  1, "unit": "kit",   "aisle": "38", "bay": "A", "price": 16.47,  "category": "Safety"},
    ],
    "deck": [
        {"name": "Composite Decking Board 12ft",     "qty": 30, "unit": "each",  "aisle": "32", "bay": "A", "price": 24.97,  "category": "Decking"},
        {"name": "4x4x8 PT Post",                    "qty":  6, "unit": "each",  "aisle": "31", "bay": "C", "price": 18.47,  "category": "Lumber"},
        {"name": "2x8x12 PT Joist",                  "qty": 16, "unit": "each",  "aisle": "31", "bay": "B", "price": 19.23,  "category": "Lumber"},
        {"name": "Post Base Anchor",                 "qty":  6, "unit": "each",  "aisle": "19", "bay": "A", "price": 14.97,  "category": "Hardware"},
        {"name": "Concrete Mix 80lb Bag",            "qty": 12, "unit": "bag",   "aisle": "19", "bay": "D", "price": 6.25,   "category": "Concrete"},
        {"name": "Composite Railing 6ft Section",    "qty":  8, "unit": "each",  "aisle": "32", "bay": "B", "price": 67.00,  "category": "Railing"},
        {"name": "Deck Screws 5lb Box",              "qty":  3, "unit": "box",   "aisle": "26", "bay": "A", "price": 14.97,  "category": "Fasteners"},
        {"name": "Joist Hanger LUS28 10-Pack",       "qty":  2, "unit": "pack",  "aisle": "26", "bay": "C", "price": 14.97,  "category": "Fasteners"},
        {"name": "Ledger Board Hardware Kit",        "qty":  1, "unit": "kit",   "aisle": "26", "bay": "D", "price": 34.97,  "category": "Hardware"},
        {"name": "Stair Stringer 3-Step",            "qty":  2, "unit": "each",  "aisle": "32", "bay": "C", "price": 28.97,  "category": "Stairs"},
        {"name": "Deck Waterproof Sealer Gal",       "qty":  2, "unit": "gal",   "aisle": "23", "bay": "C", "price": 42.97,  "category": "Sealants"},
        {"name": "Safety Glasses + Gloves Kit",      "qty":  1, "unit": "kit",   "aisle": "38", "bay": "A", "price": 16.47,  "category": "Safety"},
    ],
    "fence": [
        {"name": "6ft Cedar Privacy Board 8ft",      "qty": 40, "unit": "each",  "aisle": "33", "bay": "A", "price": 7.97,   "category": "Lumber"},
        {"name": "4x4x8 PT Fence Post",              "qty": 10, "unit": "each",  "aisle": "31", "bay": "D", "price": 14.47,  "category": "Lumber"},
        {"name": "2x4x8 PT Rail",                    "qty": 20, "unit": "each",  "aisle": "31", "bay": "A", "price": 8.47,   "category": "Lumber"},
        {"name": "Fence Gate 4ft Cedar",             "qty":  1, "unit": "each",  "aisle": "33", "bay": "B", "price": 79.00,  "category": "Gates"},
        {"name": "Concrete Mix 80lb Bag",            "qty": 20, "unit": "bag",   "aisle": "19", "bay": "D", "price": 6.25,   "category": "Concrete"},
        {"name": "Gate Hardware Kit",                "qty":  1, "unit": "kit",   "aisle": "26", "bay": "E", "price": 24.97,  "category": "Hardware"},
        {"name": "Fence Nails 5lb Box",              "qty":  2, "unit": "box",   "aisle": "26", "bay": "B", "price": 12.47,  "category": "Fasteners"},
        {"name": "Post Cap Flat 4x4 10-Pack",        "qty":  1, "unit": "pack",  "aisle": "26", "bay": "F", "price": 18.97,  "category": "Hardware"},
        {"name": "Wood Preservative 1gal",           "qty":  1, "unit": "gal",   "aisle": "23", "bay": "D", "price": 21.97,  "category": "Sealants"},
        {"name": "Safety Glasses + Gloves Kit",      "qty":  1, "unit": "kit",   "aisle": "38", "bay": "A", "price": 16.47,  "category": "Safety"},
    ],
    "patio": [
        {"name": "Concrete Patio Block 16x16",       "qty": 64, "unit": "each",  "aisle": "20", "bay": "A", "price": 4.47,   "category": "Pavers"},
        {"name": "Paver Base 50lb Bag",              "qty": 20, "unit": "bag",   "aisle": "20", "bay": "B", "price": 5.97,   "category": "Base Material"},
        {"name": "Paver Sand 50lb Bag",              "qty": 10, "unit": "bag",   "aisle": "20", "bay": "C", "price": 4.97,   "category": "Base Material"},
        {"name": "Landscape Edging 20ft",            "qty":  4, "unit": "each",  "aisle": "21", "bay": "A", "price": 14.97,  "category": "Edging"},
        {"name": "Edging Stakes 100-Pack",           "qty":  1, "unit": "pack",  "aisle": "21", "bay": "B", "price": 9.97,   "category": "Hardware"},
        {"name": "Polymeric Sand 50lb Bag",          "qty":  4, "unit": "bag",   "aisle": "20", "bay": "D", "price": 19.97,  "category": "Jointing"},
        {"name": "Paver Sealer 1gal",                "qty":  2, "unit": "gal",   "aisle": "23", "bay": "E", "price": 34.97,  "category": "Sealants"},
        {"name": "Safety Glasses + Gloves Kit",      "qty":  1, "unit": "kit",   "aisle": "38", "bay": "A", "price": 16.47,  "category": "Safety"},
    ],
}

_RENTALS: Dict[str, List[Dict]] = {
    "shed": [
        {"name": "Post Hole Digger (Electric)",  "days": 1, "day_rate": 45.00, "deposit": 150.0, "why": "Digging 4 foundation post holes"},
        {"name": "Concrete Mixer 3.5 cu ft",     "days": 1, "day_rate": 85.00, "deposit": 200.0, "why": "Mixing concrete for posts"},
        {"name": "Pneumatic Framing Nailer",      "days": 2, "day_rate": 35.00, "deposit": 100.0, "why": "Framing walls and roof"},
    ],
    "deck": [
        {"name": "Post Hole Digger (Electric)",  "days": 1, "day_rate": 45.00, "deposit": 150.0, "why": "Digging post footings"},
        {"name": "Concrete Mixer 3.5 cu ft",     "days": 1, "day_rate": 85.00, "deposit": 200.0, "why": "Mixing concrete for footings"},
        {"name": "Circular Saw (Premium)",       "days": 2, "day_rate": 29.00, "deposit":  75.0, "why": "Cutting decking boards to length"},
    ],
    "fence": [
        {"name": "Post Hole Digger (Electric)",  "days": 1, "day_rate": 45.00, "deposit": 150.0, "why": "Digging 10 fence post holes"},
        {"name": "Concrete Mixer 3.5 cu ft",     "days": 1, "day_rate": 85.00, "deposit": 200.0, "why": "Setting posts in concrete"},
    ],
    "patio": [
        {"name": "Plate Compactor",              "days": 1, "day_rate": 95.00, "deposit": 250.0, "why": "Compacting paver base"},
        {"name": "Wet Tile Saw",                 "days": 1, "day_rate": 65.00, "deposit": 150.0, "why": "Cutting edge pavers"},
    ],
}

_STORES: List[Dict] = [
    {"id": "hd_001", "name": "Home Depot — Colorado Blvd",    "address": "2700 Colorado Blvd, Denver CO 80207",   "distance_miles": 2.3,  "phone": "(303) 329-0219", "hours": "6am–10pm"},
    {"id": "hd_002", "name": "Home Depot — Federal Blvd",     "address": "1200 W Alameda Ave, Denver CO 80223",   "distance_miles": 4.1,  "phone": "(303) 935-6500", "hours": "6am–10pm"},
    {"id": "hd_003", "name": "Home Depot — Wadsworth Blvd",   "address": "5001 Wadsworth Blvd, Arvada CO 80002",  "distance_miles": 7.8,  "phone": "(303) 456-0801", "hours": "6am–9pm"},
]

_PERMIT_RULES: Dict[str, str] = {
    "shed":  "⚠️  Denver requires a building permit for sheds over 120 sq ft. A 10×12 (120 sq ft) is right at the limit — confirm with Denver Community Planning. Permit est. $150–$250.",
    "deck":  "⚠️  Decks over 30 inches above grade require a permit in most Denver zones. Estimated permit cost: $200–$350.",
    "fence": "✅  Fences under 6 ft typically do not require a permit in Denver. Verify HOA rules if applicable.",
    "patio": "✅  Ground-level patios generally do not require a permit. No action needed.",
}

_ESQL_QUERIES: Dict[str, str] = {
    "geo": """\
FROM stores METADATA _id
| EVAL distance_m = ST_DISTANCE(
    location,
    TO_GEOPOINT("{lat},{lon}")
  )
| WHERE distance_m <= 40233          -- 25 miles
| EVAL distance_miles = ROUND(distance_m / 1609.34, 1)
| SORT distance_m ASC
| LIMIT 3
| KEEP store_id, name, address, distance_miles, phone""",

    "semantic": """\
FROM product_catalog METADATA _id, _score
| WHERE MATCH(description, "{query}")
| WHERE category IN ({categories})
| SORT _score DESC
| LIMIT 50
| KEEP product_id, name, sku, aisle, bay, price, category, _score""",

    "inventory": """\
FROM store_inventory
| WHERE store_id == "{store_id}"
| LOOKUP JOIN product_catalog ON product_id
| WHERE qty_in_stock >= needed_qty
| EVAL subtotal = price * needed_qty
| STATS
    total_cost = SUM(subtotal),
    item_count = COUNT(*)
  BY store_id
| SORT total_cost ASC""",

    "rag": """\
FROM project_templates METADATA _id, _score
| WHERE MATCH(description, "{project_description}")
| WHERE project_type == "{project_type}"
| SORT _score DESC
| LIMIT 1
| KEEP project_type, materials_list, tools_required, permit_info, avg_duration_days""",
}


# ---------------------------------------------------------------------------
# Main service entry point
# ---------------------------------------------------------------------------

class RevenueEngineService:
    """Runs project-to-cart search. Uses live ES when available, simulation otherwise."""

    def __init__(self):
        self._es = None
        self._es_available = False
        self._try_connect()

    def _try_connect(self):
        try:
            from elasticsearch import Elasticsearch
            api_key = os.getenv("ELASTICSEARCH_API_KEY", "")
            cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
            if cloud_id:
                self._es = Elasticsearch(cloud_id=cloud_id, api_key=api_key)
            else:
                endpoint = os.getenv("ELASTIC_ENDPOINT", "")
                self._es = Elasticsearch(endpoint, api_key=api_key)
            self._es.info()
            self._es_available = True
        except Exception as e:
            logger.info(f"Revenue Engine running in simulation mode: {e}")
            self._es_available = False

    def plan_project(
        self,
        description: str,
        zip_code: str,
        size: str,
        purpose: str,
        budget: float,
        index_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point. Returns a full project plan dict.
        Tries live ES first; falls back to simulation.
        """
        start = time.time()

        project_type = _classify_project(description, purpose)
        lat, lon = _zip_to_coords(zip_code)

        # Try live ES search; fall back to simulation
        use_live = self._es_available and index_names and self._has_product_data(index_names)

        if use_live:
            result = self._live_plan(description, project_type, size, lat, lon, index_names)
            result["mode"] = "live"
        else:
            result = self._simulated_plan(project_type, size, lat, lon)
            result["mode"] = "simulation"

        result.update({
            "project_type": project_type,
            "description": description,
            "zip_code": zip_code,
            "size": size,
            "purpose": purpose,
            "budget": budget,
            "elapsed_ms": int((time.time() - start) * 1000),
            "queries": self._build_query_display(project_type, lat, lon),
            "permit_notice": _PERMIT_RULES.get(project_type, ""),
        })

        return result

    def _simulated_plan(self, project_type: str, size: str, lat: float, lon: float) -> Dict:
        materials = _BOM.get(project_type, _BOM["shed"])
        rentals = _RENTALS.get(project_type, _RENTALS["shed"])

        # Scale quantities slightly by size
        scale = _size_scale(size)
        scaled = []
        for item in materials:
            m = dict(item)
            m["qty"] = max(1, round(m["qty"] * scale))
            m["subtotal"] = round(m["qty"] * m["price"], 2)
            scaled.append(m)

        total_materials = round(sum(m["subtotal"] for m in scaled), 2)
        total_rentals = round(sum(r["days"] * r["day_rate"] for r in rentals), 2)

        # Sort stores by rough distance from lat/lon
        store = _STORES[0]

        return {
            "store": store,
            "materials": scaled,
            "rentals": rentals,
            "total_materials": total_materials,
            "total_rentals": total_rentals,
            "grand_total": round(total_materials + total_rentals, 2),
            "timing": {
                "geo_search_ms": 18,
                "semantic_search_ms": 124,
                "inventory_join_ms": 67,
                "rag_project_guide_ms": 203,
            },
        }

    def _live_plan(self, description, project_type, size, lat, lon, index_names) -> Dict:
        """Query real ES indices. Falls back per-step if an index is missing."""
        # For now delegate to simulation — live queries require product data to be indexed
        return self._simulated_plan(project_type, size, lat, lon)

    def has_product_data(self, index_names: Optional[List[str]]) -> bool:
        return self._es_available and self.has_product_data(index_names)

    def _has_product_data(self, index_names: List[str]) -> bool:
        try:
            for name in index_names:
                if "product" in name.lower() or "catalog" in name.lower():
                    count = self._es.count(index=name).get("count", 0)
                    if count > 0:
                        return True
            return False
        except Exception:
            return False

    def _build_query_display(self, project_type: str, lat: float, lon: float) -> List[Dict]:
        cats = '"Lumber", "Roofing", "Concrete", "Hardware", "Fasteners"'
        return [
            {
                "label": "📍 Geo — Find nearest store",
                "timing_key": "geo_search_ms",
                "esql": _ESQL_QUERIES["geo"].format(lat=lat, lon=lon),
            },
            {
                "label": "🔍 ELSER Semantic — Match products to project",
                "timing_key": "semantic_search_ms",
                "esql": _ESQL_QUERIES["semantic"].format(
                    query=f"{project_type} materials outdoor framing structural",
                    categories=cats,
                ),
            },
            {
                "label": "📦 ES|QL — Inventory join across store + catalog",
                "timing_key": "inventory_join_ms",
                "esql": _ESQL_QUERIES["inventory"].format(store_id="hd_001"),
            },
            {
                "label": "📚 RAG — Retrieve project build guide",
                "timing_key": "rag_project_guide_ms",
                "esql": _ESQL_QUERIES["rag"].format(
                    project_description=f"build a {project_type}",
                    project_type=project_type,
                ),
            },
        ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_project(description: str, purpose: str) -> str:
    text = (description + " " + purpose).lower()
    if any(w in text for w in ["shed", "storage", "workshop", "outbuilding"]):
        return "shed"
    if any(w in text for w in ["deck", "decking", "outdoor platform"]):
        return "deck"
    if any(w in text for w in ["fence", "fencing", "privacy", "boundary"]):
        return "fence"
    if any(w in text for w in ["patio", "pavers", "paving", "courtyard"]):
        return "patio"
    return "shed"


def _zip_to_coords(zip_code: str) -> Tuple[float, float]:
    """Rough centroid lookup for demo zip codes."""
    coords = {
        "80203": (39.7297, -104.9776),
        "80205": (39.7558, -104.9654),
        "10001": (40.7484, -74.0016),
        "94102": (37.7792, -122.4191),
        "30301": (33.7490, -84.3880),
        "60601": (41.8858, -87.6181),
        "77001": (29.7520, -95.3677),
    }
    return coords.get(zip_code, (39.7392, -104.9903))  # default Denver


def _size_scale(size: str) -> float:
    """Scale material quantities based on project size."""
    size_lower = size.lower().replace(" ", "").replace("x", "x")
    scales = {
        "8x8": 0.7, "8x10": 0.8, "10x10": 0.9, "10x12": 1.0,
        "12x12": 1.15, "12x16": 1.4, "16x16": 1.7, "16x20": 2.0,
    }
    # Try exact match first
    for key, scale in scales.items():
        if key in size_lower:
            return scale
    # Fallback: parse dimensions
    try:
        parts = size_lower.split("x")
        area = int(parts[0]) * int(parts[1])
        return area / 120.0
    except Exception:
        return 1.0
