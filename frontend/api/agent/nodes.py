import json
import re
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os
import uuid

from api.models.schemas import Requirements, CanonicalProduct, MarketplaceOffer
from api.agent.prompts import REQUIREMENT_EXTRACTION_PROMPT, DECISION_AGENT_PROMPT
from api.services.search_service import search_live_products

# LLM Initialization - Disabled due to API issues
llm = None
print("INFO: Google Gemini LLM disabled - using fallback logic")
        
tavily_api_key = os.getenv("TAVILY_API_KEY")

def extract_requirements(state: dict) -> Dict[str, Any]:
    timeline = state.get("timeline", [])
    timeline.append("[PARSING] User goal received. Extracting constraints...")
    goal = state.get("goal", "")
    
    if not llm:
        # Fallback to simple parsing
        search_query = goal
        category = "general"
        budget_max = 999999
        hard_constraints = {}
        preferences = []
        
        # Simple keyword-based parsing
        if "under" in goal.lower():
            parts = goal.lower().split("under")
            if len(parts) > 1:
                budget_str = parts[1].strip()
                # Extract numbers from string
                import re
                numbers = re.findall(r'\d+', budget_str)
                if numbers:
                    budget_max = float(numbers[0])
        
        reqs = Requirements(
            search_query=search_query,
            category=category,
            budget_max=budget_max,
            hard_constraints=hard_constraints,
            preferences=preferences
        )
        return {"requirements": reqs, "timeline": timeline}
    
    prompt = REQUIREMENT_EXTRACTION_PROMPT.format(goal=goal)
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        content = response.content
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```', '', content)
        req_dict = json.loads(content)
        reqs = Requirements(**req_dict)
    except Exception as e:
        print(f"Error parsing LLM output: {e}, Content: {response.content}")
        # Fallback to simple parsing
        search_query = goal
        category = "general"
        budget_max = 999999
        hard_constraints = {}
        preferences = []
        reqs = Requirements(
            search_query=search_query,
            category=category,
            budget_max=budget_max,
            hard_constraints=hard_constraints,
            preferences=preferences
        )
        
    return {"requirements": reqs, "timeline": timeline}

def search_coordination(state: dict) -> Dict[str, Any]:
    timeline = state.get("timeline", [])
    reqs = state.get("requirements")
    query = reqs.search_query if reqs and reqs.search_query else state.get("goal", "buy products online")
    budget_max = reqs.budget_max if reqs else 999999
    
    timeline.append(f"[SEARCHING] Executing dynamic search via SerpApi for: '{query}' (budget: ₹{budget_max})")
    
    offers = []
    
    try:
        raw_results = search_live_products(query, budget_max)
        offers = [MarketplaceOffer(**item) if isinstance(item, dict) else item for item in raw_results]
        timeline.append(f"[SEARCH COMPLETE] Found {len(offers)} raw product offers from marketplaces.")
    except Exception as e:
        print(f"Error during SerpApi search: {e}")
        timeline.append(f"[SEARCH ERROR] {str(e)[:100]}...")
    
    if not offers:
        timeline.append("[SEARCH FAILED] No offers could be retrieved from SerpApi. Using fallback data.")
        # Add some fallback data for demo purposes
        if "headphone" in query.lower() or "headphones" in query.lower():
            offers = [
                MarketplaceOffer(
                    id=str(uuid.uuid4()),
                    store="Amazon.in",
                    title="Sony WH-CH520 Wireless Headphones",
                    brand="Sony",
                    price=2999.0,
                    specs={"battery_hours": 50, "noise_cancellation": True, "wireless": True, "color": "Black"},
                    rating=4.5,
                    delivery_days=3,
                    in_stock=True,
                    product_url="https://amazon.in/demo",
                    thumbnail="https://m.media-amazon.com/images/I/51BbG9c6RBL._SX679_.jpg"
                ),
                MarketplaceOffer(
                    id=str(uuid.uuid4()),
                    store="Flipkart",
                    title="JBL Tune 510BT Wireless Headphones",
                    brand="JBL",
                    price=2499.0,
                    specs={"battery_hours": 40, "noise_cancellation": False, "wireless": True, "color": "Blue"},
                    rating=4.3,
                    delivery_days=2,
                    in_stock=True,
                    product_url="https://flipkart.com/demo",
                    thumbnail="https://assets.myntassets.com/h_720,q_90,w_540/v1/assets/products/12938179/2023/7/18/d7d9c62d-7566-45d8-a408-508c99d66a971689673699368-JBL-Tune-510BT-Wireless-Headphones-1.jpg"
                ),
                MarketplaceOffer(
                    id=str(uuid.uuid4()),
                    store="Amazon.in",
                    title="Boat Rockerz 450 Bluetooth Headphones",
                    brand="Boat",
                    price=1999.0,
                    specs={"battery_hours": 15, "noise_cancellation": False, "wireless": True, "color": "Red"},
                    rating=4.0,
                    delivery_days=4,
                    in_stock=True,
                    product_url="https://amazon.in/demo",
                    thumbnail="https://m.media-amazon.com/images/I/51K2F5Jb0eL._SX679_.jpg"
                )
            ]
        else:
            # Generic fallback for other products - use clean placeholder URL
            offers = [
                MarketplaceOffer(
                    id=str(uuid.uuid4()),
                    store="Amazon.in",
                    title=f"Product for {query}",
                    brand="Brand",
                    price=budget_max * 0.5,
                    specs={"general": "Standard specs"},
                    rating=4.0,
                    delivery_days=3,
                    in_stock=True,
                    product_url="https://demo.com",
                    thumbnail="https://placehold.co/400x300/e2e8f0/1e293b?text=Product"
                )
            ]
        
    return {"raw_offers": offers, "timeline": timeline}

def normalize_and_deduplicate(state: dict) -> Dict[str, Any]:
    timeline = state.get("timeline", [])
    timeline.append("[NORMALIZING] Aligning schemas to canonical fields...")
    timeline.append("[DEDUPLICATING] Grouping identical products across stores...")
    
    raw_offers = state.get("raw_offers", [])
    grouped: Dict[str, List[Any]] = {}
    
    for offer in raw_offers:
        # Create a normalized key based on brand and simplified title
        normalized_title = offer.title.lower()
        # Remove common prefixes/suffixes
        remove_words = ["wireless", "bluetooth", "bt", "pro", "plus", "max", "ultra", "premium", "hd", "4k", "gaming", "smart"]
        for word in remove_words:
            normalized_title = normalized_title.replace(word, "")
        
        # Extract main product name (first few words)
        words = normalized_title.split()
        if len(words) > 4:
            simplified_title = " ".join(words[:4])
        else:
            simplified_title = normalized_title
        
        # Clean up extra spaces
        simplified_title = simplified_title.strip()
        simplified_title = re.sub(r'\s+', ' ', simplified_title)
        
        key = f"{offer.brand.lower()}_{simplified_title}"
        
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(offer)
        
    canonicals = []
    for key, offers in grouped.items():
        # Find the best offer (lowest price, in stock)
        valid_offers = [o for o in offers if o.in_stock]
        if not valid_offers:
            valid_offers = offers  # Fall back to all offers if none are in stock
        
        if not valid_offers:
            continue
            
        best_offer = min(valid_offers, key=lambda x: x.price)
        
        # Combine specs from all offers
        combined_specs = {}
        for offer in offers:
            if offer.specs:
                combined_specs.update(offer.specs)
        
        # Use best offer's specs as base, update with combined specs
        final_specs = best_offer.specs.copy() if best_offer.specs else {}
        final_specs.update(combined_specs)
        
        # Get thumbnail from best offer (or use fallback if None)
        thumbnail = best_offer.thumbnail or "https://via.placeholder.com/300x300?text=No+Image"
        
        cp = CanonicalProduct(
            canonical_id=key,
            brand=best_offer.brand,
            model=best_offer.title,
            best_price=best_offer.price,
            best_store=best_offer.store,
            specs=final_specs,
            rating=best_offer.rating,
            delivery_days=best_offer.delivery_days,
            product_url=best_offer.product_url,
            thumbnail=thumbnail,
            all_offers=offers
        )
        canonicals.append(cp)
        
    timeline.append(f"[NORMALIZED] Consolidated {len(raw_offers)} offers into {len(canonicals)} unique products.")
    return {"canonical_products": canonicals, "timeline": timeline}

def apply_constraints(state: dict) -> Dict[str, Any]:
    timeline = state.get("timeline", [])
    reqs = state.get("requirements")
    canonical_products = state.get("canonical_products", [])
    filtered = []
    rejected = []
    
    for product in canonical_products:
        reasons = []
        
        # Budget constraint
        if product.best_price > reqs.budget_max:
            reasons.append(f"Exceeds budget (₹{product.best_price} > ₹{reqs.budget_max})")
        
        # Apply all hard constraints
        for constraint_key, constraint_val in reqs.hard_constraints.items():
            product_val = product.specs.get(constraint_key)
            
            if constraint_key.endswith("_min"):
                # Minimum constraint
                base_key = constraint_key.replace("_min", "")
                if product_val is not None and product_val < constraint_val:
                    reasons.append(f"{base_key.replace('_', ' ').title()} too low ({product_val} < {constraint_val})")
                    
            elif constraint_key.endswith("_max"):
                # Maximum constraint
                base_key = constraint_key.replace("_max", "")
                if product_val is not None and product_val > constraint_val:
                    reasons.append(f"{base_key.replace('_', ' ').title()} too high ({product_val} > {constraint_val})")
                    
            elif isinstance(constraint_val, bool):
                # Boolean constraint
                if product_val is not None and product_val != constraint_val:
                    feature_name = constraint_key.replace("_", " ").title()
                    if constraint_val:
                        reasons.append(f"Missing {feature_name}")
                    else:
                        reasons.append(f"Has {feature_name} (not allowed)")
                        
            elif isinstance(constraint_val, str):
                # String constraint (exact match)
                if product_val is not None and str(product_val).lower() != constraint_val.lower():
                    reasons.append(f"{constraint_key.replace('_', ' ').title()} mismatch")
        
        if reasons:
            rejected.append({"product": product.dict(), "reasons": reasons})
        else:
            filtered.append(product)
            
    timeline.append(f"[CONSTRAINTS APPLIED] {len(rejected)} rejected, {len(filtered)} passed.")
    return {"filtered_products": filtered, "rejected_products": rejected, "timeline": timeline}

def score_products(state: dict) -> Dict[str, Any]:
    timeline = state.get("timeline", [])
    timeline.append("[SCORING (100pt)] Running deterministic weighted scoring...")
    scored = []
    reqs = state.get("requirements")
    filtered_products = state.get("filtered_products", [])
    
    for product in filtered_products:
        score = 30  # Base score
        
        # Price scoring (max 25 points)
        # Lower price relative to budget gets higher score
        price_ratio = 1 - (product.best_price / reqs.budget_max) if reqs.budget_max > 0 and reqs.budget_max > product.best_price else 0
        score += max(0, min(25, 25 * price_ratio * 1.5))
        
        # Rating scoring (max 15 points)
        score += (product.rating / 5.0) * 15
        
        # Delivery speed scoring (max 10 points)
        # Faster delivery gets higher score
        if product.delivery_days <= 1:
            score += 10
        elif product.delivery_days <= 3:
            score += 7
        elif product.delivery_days <= 7:
            score += 3
        else:
            score += 0
        
        # Product-specific feature scoring based on specs
        # Battery scoring for electronics
        battery = product.specs.get("battery_hours", 0)
        if battery > 0:
            score += min(10, (battery / 50) * 10)  # Up to 10 points for good battery
        
        # RAM scoring for laptops/phones
        ram = product.specs.get("ram_gb", 0)
        if ram > 0:
            score += min(8, (ram / 16) * 8)  # Up to 8 points for more RAM
        
        # Storage scoring
        storage = product.specs.get("storage_gb", 0)
        if storage > 0:
            score += min(7, (storage / 512) * 7)  # Up to 7 points for more storage
        
        # Brand preference scoring (max 15 points)
        pref_score = 0
        if reqs.preferences:
            for pref in reqs.preferences:
                if pref.startswith("brand_"):
                    brand_name = pref.replace("brand_", "").lower()
                    if brand_name in product.brand.lower():
                        pref_score += 15  # High score for exact brand match
                        break
                elif pref.startswith("color_"):
                    color_name = pref.replace("color_", "").lower()
                    product_color = str(product.specs.get("color", "")).lower()
                    if color_name in product_color:
                        pref_score += 10  # Good score for color preference
                elif pref in product.specs:
                    # Generic feature preference
                    pref_score += 8
        
        score += min(15, pref_score)  # Cap preference score
        
        # Ensure score is between 0-100
        score = max(0, min(100, score))
        product.score = round(score, 1)
        scored.append(product)
        
    scored.sort(key=lambda x: x.score, reverse=True)
    timeline.append(f"[SCORING COMPLETE] Top score: {scored[0].score if scored else 'N/A'}")
    return {"top_candidates": scored, "timeline": timeline}

def decision_agent(state: dict) -> Dict[str, Any]:
    timeline = state.get("timeline", [])
    top_candidates = state.get("top_candidates", [])
    
    if not top_candidates:
        timeline.append("[DECISION FAILED] No candidates passed constraints.")
        return {"timeline": timeline}
        
    timeline.append("[DECISION READY] Agent comparing top candidates and generating rationale.")
    winner = top_candidates[0]
    
    if len(top_candidates) > 1:
        runnerup = top_candidates[1]
        
        # Generate rationale based on comparison
        price_diff = winner.best_price - runnerup.best_price
        score_diff = winner.score - runnerup.score
        
        if price_diff < 0:
            price_text = f"₹{abs(price_diff)} cheaper"
        elif price_diff > 0:
            price_text = f"₹{price_diff} more expensive"
        else:
            price_text = "same price"
            
        # Check for key differences
        rationale_parts = []
        
        if score_diff >= 5:
            rationale_parts.append(f"significantly higher score ({winner.score:.1f} vs {runnerup.score:.1f})")
        elif score_diff > 0:
            rationale_parts.append(f"better overall score ({winner.score:.1f} vs {runnerup.score:.1f})")
            
        # Check rating
        if winner.rating > runnerup.rating + 0.3:
            rationale_parts.append(f"higher rating ({winner.rating:.1f}★ vs {runnerup.rating:.1f}★)")
            
        # Check delivery
        if winner.delivery_days < runnerup.delivery_days:
            rationale_parts.append(f"faster delivery ({winner.delivery_days} vs {runnerup.delivery_days} days)")
            
        if rationale_parts:
            rationale = f"{winner.brand} {winner.model} is recommended over {runnerup.brand} {runnerup.model} because it offers {', '.join(rationale_parts)} while being {price_text}."
        else:
            rationale = f"{winner.brand} {winner.model} is the top choice with a score of {winner.score:.1f}, offering good value at ₹{winner.best_price}."
    else:
        rationale = f"{winner.brand} {winner.model} is the only product that met all your constraints, scoring {winner.score:.1f} at ₹{winner.best_price}."
        
    return {"winner": winner, "tradeoff_rationale": rationale, "timeline": timeline}
