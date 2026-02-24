"""
Domain Keyword Library

Pre-defined keyword libraries for various business domains.
Used to seed realistic, domain-specific content into generated data based on search narratives.
"""

import random
from typing import Dict, List, Any


# Domain-specific keyword libraries
DOMAIN_LIBRARIES = {
    "food_beverage": {
        "cuisines": [
            "Italian", "Mexican", "Chinese", "Thai", "French", "Japanese",
            "Mediterranean", "American", "Korean", "Vietnamese", "Greek", "Indian",
            "Spanish", "Lebanese", "Brazilian", "Moroccan"
        ],
        "dishes": [
            "pasta", "pizza", "sushi", "tacos", "curry", "steak", "salad",
            "burgers", "sandwiches", "seafood", "noodles", "rice bowls",
            "soup", "appetizers", "desserts", "entrees", "tapas", "dim sum"
        ],
        "contexts": [
            "restaurant", "catering", "food truck", "cafe", "bistro", "diner",
            "eatery", "kitchen", "bakery", "bar", "grill", "tavern",
            "gastropub", "pizzeria", "trattoria", "brasserie"
        ],
        "descriptors": [
            "authentic", "fresh", "homemade", "gourmet", "artisan",
            "traditional", "handcrafted", "organic", "locally-sourced",
            "farm-to-table", "seasonal", "signature", "specialty"
        ],
        "occasions": [
            "dinner service", "lunch special", "brunch menu", "takeout",
            "delivery", "catering event", "dining experience", "happy hour",
            "tasting menu", "prix fixe", "wine pairing"
        ]
    },

    "fitness": {
        "activities": [
            "yoga", "running", "cycling", "weightlifting", "CrossFit",
            "pilates", "HIIT", "spinning", "boxing", "swimming",
            "kickboxing", "barre", "rowing", "martial arts", "dance fitness"
        ],
        "products": [
            "activewear", "gym apparel", "workout clothes", "athletic wear",
            "sports gear", "fitness equipment", "training accessories",
            "exercise gear", "performance wear", "athletic clothing"
        ],
        "contexts": [
            "fitness center", "gym", "sports club", "wellness studio",
            "training facility", "health club", "yoga studio", "CrossFit box",
            "boutique studio", "athletic center", "recreation center"
        ],
        "descriptors": [
            "performance", "breathable", "flexible", "durable",
            "moisture-wicking", "comfortable", "supportive", "lightweight",
            "high-impact", "compression", "ergonomic", "versatile"
        ],
        "benefits": [
            "muscle building", "weight loss", "cardio health", "flexibility",
            "strength training", "endurance", "recovery", "wellness",
            "conditioning", "mobility", "stamina", "body composition"
        ]
    },

    "retail": {
        "products": [
            "clothing", "accessories", "footwear", "jewelry", "home decor",
            "electronics", "gadgets", "furniture", "cosmetics", "bags",
            "watches", "sunglasses", "handbags", "scarves", "belts"
        ],
        "styles": [
            "modern", "vintage", "minimalist", "luxury", "casual", "formal",
            "bohemian", "contemporary", "classic", "trendy", "elegant",
            "chic", "sophisticated", "edgy", "timeless"
        ],
        "contexts": [
            "boutique", "department store", "online shop", "showroom",
            "outlet", "mall", "marketplace", "retail store", "shop",
            "fashion house", "concept store", "pop-up shop"
        ],
        "descriptors": [
            "trendy", "affordable", "premium", "exclusive", "versatile",
            "handmade", "designer", "limited-edition", "curated",
            "stylish", "quality", "authentic", "unique"
        ],
        "occasions": [
            "everyday wear", "special occasion", "work attire", "weekend casual",
            "formal event", "seasonal collection", "holiday gift",
            "wardrobe essentials", "statement pieces"
        ]
    },

    "real_estate": {
        "property_types": [
            "single-family home", "condo", "townhouse", "apartment",
            "luxury estate", "commercial space", "office building", "land",
            "multi-family", "ranch", "cottage", "bungalow", "penthouse"
        ],
        "features": [
            "open floor plan", "modern kitchen", "master suite", "backyard",
            "pool", "garage", "hardwood floors", "updated bathrooms",
            "granite countertops", "stainless appliances", "walk-in closet",
            "fireplace", "deck", "patio", "finished basement"
        ],
        "locations": [
            "downtown", "suburban", "waterfront", "historic district",
            "gated community", "school district", "walkable neighborhood",
            "city center", "residential area", "commuter-friendly"
        ],
        "descriptors": [
            "spacious", "renovated", "move-in ready", "charming", "contemporary",
            "pristine", "well-maintained", "upgraded", "stunning",
            "immaculate", "turnkey", "elegant", "inviting"
        ],
        "contexts": [
            "listing", "open house", "property showcase", "virtual tour",
            "market analysis", "neighborhood guide", "property brochure",
            "home showing", "real estate marketing"
        ]
    },

    "healthcare": {
        "services": [
            "primary care", "urgent care", "specialty clinic", "diagnostic imaging",
            "laboratory services", "physical therapy", "mental health", "wellness",
            "preventive care", "chronic disease management", "telehealth"
        ],
        "specialties": [
            "cardiology", "orthopedics", "pediatrics", "dermatology",
            "neurology", "oncology", "women's health", "dentistry",
            "ophthalmology", "gastroenterology", "endocrinology"
        ],
        "contexts": [
            "hospital", "clinic", "medical center", "health system",
            "physician practice", "urgent care center", "outpatient facility",
            "wellness center", "specialty practice", "healthcare facility"
        ],
        "descriptors": [
            "comprehensive", "patient-centered", "evidence-based", "compassionate",
            "advanced", "preventive", "personalized", "accessible",
            "coordinated", "integrated", "holistic", "quality"
        ],
        "benefits": [
            "improved outcomes", "faster recovery", "better quality of life",
            "preventive care", "chronic disease management", "wellness support",
            "pain relief", "health optimization", "disease prevention"
        ]
    },

    "technology": {
        "products": [
            "software", "hardware", "cloud services", "mobile apps",
            "SaaS platform", "enterprise solutions", "API services",
            "data analytics", "AI tools", "security software"
        ],
        "features": [
            "automation", "integration", "scalability", "security",
            "analytics", "reporting", "collaboration", "workflow",
            "customization", "real-time", "cloud-based", "mobile-first"
        ],
        "contexts": [
            "tech company", "startup", "enterprise", "SMB market",
            "developer tools", "business software", "consumer apps",
            "IT solutions", "digital transformation"
        ],
        "descriptors": [
            "innovative", "cutting-edge", "scalable", "reliable",
            "user-friendly", "robust", "secure", "efficient",
            "intuitive", "powerful", "flexible", "modern"
        ],
        "benefits": [
            "productivity gains", "cost savings", "automation",
            "streamlined workflows", "better insights", "competitive advantage",
            "digital transformation", "operational efficiency"
        ]
    },

    "professional_services": {
        "services": [
            "consulting", "legal services", "accounting", "financial planning",
            "marketing services", "HR consulting", "business advisory",
            "tax preparation", "audit services", "management consulting"
        ],
        "specialties": [
            "strategy", "operations", "compliance", "risk management",
            "mergers & acquisitions", "corporate law", "tax strategy",
            "financial advisory", "business transformation"
        ],
        "contexts": [
            "consulting firm", "law firm", "accounting firm", "advisory practice",
            "professional services firm", "boutique consultancy",
            "business services", "corporate advisory"
        ],
        "descriptors": [
            "experienced", "trusted", "strategic", "results-driven",
            "client-focused", "expert", "specialized", "comprehensive",
            "tailored", "proven", "professional", "reliable"
        ],
        "benefits": [
            "business growth", "risk mitigation", "compliance assurance",
            "strategic planning", "operational excellence", "cost optimization",
            "competitive positioning", "expert guidance"
        ]
    },

    "hospitality": {
        "services": [
            "accommodations", "dining", "events", "catering",
            "conference facilities", "spa services", "concierge",
            "room service", "business center", "recreation"
        ],
        "amenities": [
            "pool", "fitness center", "restaurant", "bar", "spa",
            "meeting rooms", "free WiFi", "parking", "breakfast",
            "room service", "valet", "business center"
        ],
        "contexts": [
            "hotel", "resort", "inn", "bed and breakfast",
            "vacation rental", "conference center", "event venue",
            "boutique hotel", "luxury resort", "business hotel"
        ],
        "descriptors": [
            "luxurious", "comfortable", "welcoming", "elegant",
            "modern", "historic", "charming", "upscale",
            "family-friendly", "romantic", "convenient", "stylish"
        ],
        "experiences": [
            "relaxation", "business travel", "family vacation",
            "romantic getaway", "conference attendance", "special event",
            "weekend escape", "destination wedding"
        ]
    },

    "fashion": {
        "categories": [
            "apparel", "footwear", "accessories", "jewelry",
            "outerwear", "activewear", "formal wear", "casual wear",
            "swimwear", "lingerie", "handbags", "eyewear"
        ],
        "styles": [
            "contemporary", "classic", "trendy", "minimalist",
            "bohemian", "edgy", "elegant", "casual chic",
            "street style", "preppy", "romantic", "avant-garde"
        ],
        "occasions": [
            "everyday", "work", "evening", "casual weekend",
            "formal event", "cocktail party", "beach vacation",
            "date night", "business casual", "athleisure"
        ],
        "descriptors": [
            "stylish", "fashionable", "on-trend", "timeless",
            "versatile", "statement", "effortless", "sophisticated",
            "comfortable", "flattering", "quality", "designer"
        ],
        "contexts": [
            "fashion brand", "clothing line", "designer collection",
            "fashion retailer", "boutique", "online fashion",
            "seasonal collection", "capsule wardrobe"
        ]
    }
}

# Generic fallback keywords (used when domain not in library and no custom library provided)
GENERIC_KEYWORDS = {
    "primary_terms": [
        "content", "materials", "resources", "assets", "documents",
        "information", "data", "records", "files", "items"
    ],
    "contexts": [
        "organization", "business", "facility", "department", "enterprise",
        "office", "workplace", "center", "location", "site"
    ],
    "descriptors": [
        "professional", "quality", "comprehensive", "effective", "detailed",
        "accurate", "reliable", "thorough", "complete", "organized"
    ],
    "processes": [
        "operations", "workflows", "procedures", "activities", "services",
        "tasks", "functions", "processes", "management", "administration"
    ],
    "applications": [
        "business use", "organizational needs", "operational requirements",
        "professional purposes", "enterprise applications", "workflow support"
    ]
}


def get_keywords_for_domain(
    domain: str,
    custom_library: Dict[str, List[str]] = None
) -> Dict[str, List[str]]:
    """
    Get keyword library for specific domain.

    Priority order:
    1. Custom library (if provided) - generated per-demo from search scenarios
    2. Static domain library (if domain exists) - predefined keywords
    3. Generic fallback - domain-neutral keywords

    Args:
        domain: Domain name (e.g., 'food_beverage', 'fitness', 'retail')
        custom_library: Optional custom library generated for this demo

    Returns:
        Dictionary of keyword categories for the domain
    """
    import logging
    logger = logging.getLogger(__name__)

    # Priority 1: Use custom library if available (best quality)
    if custom_library and len(custom_library) > 0:
        logger.debug(f"Using custom library with {len(custom_library)} categories")
        return custom_library

    # Priority 2: Use static library if domain exists
    if domain in DOMAIN_LIBRARIES:
        logger.debug(f"Using static library for domain: {domain}")
        return DOMAIN_LIBRARIES[domain]

    # Priority 3: Generic fallback (better than "retail")
    logger.warning(f"Domain '{domain}' not in library and no custom library provided, using generic keywords")
    return GENERIC_KEYWORDS


def seed_description_with_keywords(
    scenario: Dict[str, Any],
    use_exact: bool = True,
    asset_type: str = "image",
    index: int = 0,
    custom_library: Dict[str, List[str]] = None
) -> str:
    """
    Generate a description with keywords seeded from the scenario.

    This creates natural-sounding descriptions that include the exact phrases
    or semantic concepts from the search narrative, ensuring queries return
    relevant results with good relevancy scores.

    Args:
        scenario: Search scenario from narrative with exact_phrases, semantic_phrases
        use_exact: If True, use exact phrases; if False, use semantic phrases
        asset_type: Type of asset (image, video, graphic, etc.)
        index: Document index for variation
        custom_library: Optional custom library generated for this demo

    Returns:
        Rich description with natural keyword integration
    """
    domain = scenario.get("domain", "retail")
    keywords = get_keywords_for_domain(domain, custom_library)

    if use_exact:
        # Use exact target phrase
        exact_phrases = scenario.get("exact_phrases", [])
        if not exact_phrases:
            return f"Professional {asset_type} content for marketing campaigns."

        exact_phrase = exact_phrases[index % len(exact_phrases)]

        # Get supporting keywords from library
        category_keys = list(keywords.keys())
        supporting1 = random.choice(keywords[category_keys[min(0, len(category_keys)-1)]])
        supporting2 = random.choice(keywords[category_keys[min(1, len(category_keys)-1)]])
        context = random.choice(keywords.get("contexts", ["business"]))
        descriptor = random.choice(keywords.get("descriptors", ["professional"]))

        # Template variations for natural language
        templates = [
            f"Professional {asset_type} showcasing {exact_phrase} with emphasis on {supporting1}. "
            f"{descriptor.title()} content ideal for {context} marketing campaigns featuring {supporting2}.",

            f"{descriptor.title()} {asset_type} highlighting {exact_phrase} in authentic presentation. "
            f"Perfect for {context} promotions, capturing the essence of {supporting1} and {supporting2}.",

            f"High-quality {asset_type} featuring {exact_phrase} designed for {context} advertising. "
            f"Showcases {supporting1} with {descriptor} attention to detail and {supporting2} appeal.",

            f"Compelling {asset_type} content centered on {exact_phrase}. "
            f"Combines {supporting1} with {supporting2} for impactful {context} marketing.",

            f"{descriptor.title()} marketing {asset_type} emphasizing {exact_phrase}. "
            f"Features {supporting1} in {context} setting with strong {supporting2} elements.",
        ]

        return random.choice(templates)

    else:
        # Use semantic phrase
        semantic_phrases = scenario.get("semantic_phrases", [])
        if not semantic_phrases:
            return f"Professional {asset_type} content for business marketing."

        semantic_phrase = semantic_phrases[index % len(semantic_phrases)]

        # Get supporting keywords
        category_keys = list(keywords.keys())
        supporting1 = random.choice(keywords[category_keys[min(0, len(category_keys)-1)]])
        supporting2 = random.choice(keywords[category_keys[min(1, len(category_keys)-1)]])
        context = random.choice(keywords.get("contexts", ["business"]))

        templates = [
            f"Creative {asset_type} emphasizing {semantic_phrase} through {supporting1}. "
            f"Designed for {context} campaigns with focus on {supporting2} and authentic presentation.",

            f"{asset_type.title()} content highlighting {semantic_phrase} in professional setting. "
            f"Features {supporting1} and {supporting2} perfect for {context} promotional materials.",

            f"Engaging {asset_type} that captures {semantic_phrase} with {supporting1}. "
            f"Ideal for {context} marketing, emphasizing quality {supporting2} and compelling visuals.",

            f"Professional {asset_type} showcasing {semantic_phrase} for {context} audiences. "
            f"Integrates {supporting1} with {supporting2} for maximum impact.",

            f"High-impact {asset_type} focused on {semantic_phrase}. "
            f"Perfect for {context} advertising featuring {supporting1} and {supporting2}.",
        ]

        return random.choice(templates)


def generate_noise_description(asset_type: str = "image") -> str:
    """
    Generate unrelated content for noise/contrast in search results.

    Args:
        asset_type: Type of asset

    Returns:
        Generic description not related to any search scenario
    """
    domains = ["technology", "education", "finance", "travel", "corporate"]
    contexts = ["software", "corporate", "professional", "business", "digital"]
    descriptors = ["modern", "innovative", "efficient", "streamlined", "cutting-edge"]

    domain = random.choice(domains)
    context = random.choice(contexts)
    descriptor = random.choice(descriptors)

    templates = [
        f"{descriptor.title()} {domain} {asset_type} for {context} presentations. "
        f"Clean design with minimalist aesthetic and professional styling.",

        f"Professional {context} {asset_type} for {domain} industry marketing. "
        f"Features {descriptor} design elements and contemporary visuals.",

        f"{domain.title()} focused {asset_type} with {descriptor} {context} styling. "
        f"Ideal for corporate communications and business presentations.",

        f"Contemporary {asset_type} designed for {domain} sector. "
        f"Combines {descriptor} approach with {context} professionalism.",

        f"{descriptor.title()} {asset_type} for {context} {domain} applications. "
        f"Features clean lines and modern aesthetic principles.",
    ]

    return random.choice(templates)
