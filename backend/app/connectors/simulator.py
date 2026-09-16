import json
import os
from typing import List
from app.models.schemas import MarketplaceOffer

MARKETPLACES_FILE = os.path.join(os.path.dirname(__file__), "marketplaces.json")

def get_all_offers() -> List[MarketplaceOffer]:
    if not os.path.exists(MARKETPLACES_FILE):
        return []
    with open(MARKETPLACES_FILE, 'r') as f:
        data = json.load(f)
        return [MarketplaceOffer(**item) for item in data]
