from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class MarketplaceOffer(BaseModel):
    id: str
    store: str
    title: str
    brand: str
    price: float
    specs: Dict[str, Any]
    rating: float
    delivery_days: int
    in_stock: bool
    product_url: str
    thumbnail: Optional[str] = None

class CanonicalProduct(BaseModel):
    canonical_id: str
    brand: str
    model: str
    best_price: float
    best_store: str
    specs: Dict[str, Any]
    rating: float
    delivery_days: int
    product_url: Optional[str] = None
    thumbnail: Optional[str] = None  # Will be set in normalize_and_deduplicate with fallback
    all_offers: List[MarketplaceOffer]
    score: Optional[float] = 0.0

class Requirements(BaseModel):
    search_query: str = Field(description="Optimized e-commerce search query for Tavily, e.g., 'Sony wireless headphones buy online India'")
    category: str = Field(description="The category of the product, e.g., 'wireless headphones'")
    budget_max: float = Field(description="The maximum budget in INR")
    hard_constraints: Dict[str, Any] = Field(description="Strict minimum or maximum specifications, e.g., {'battery_hours_min': 20}")
    preferences: List[str] = Field(description="Soft preferences, e.g., ['brand_sony', 'brand_jbl']")

class ShoppingState(BaseModel):
    session_id: str
    goal: str
    requirements: Optional[Requirements] = None
    raw_offers: List[MarketplaceOffer] = []
    canonical_products: List[CanonicalProduct] = []
    filtered_products: List[CanonicalProduct] = []
    rejected_products: List[Dict[str, Any]] = []
    top_candidates: List[CanonicalProduct] = []
    winner: Optional[CanonicalProduct] = None
    tradeoff_rationale: Optional[str] = None
    timeline: List[str] = []
