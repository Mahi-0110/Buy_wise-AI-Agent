from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict, Any
from app.models.schemas import Requirements, MarketplaceOffer, CanonicalProduct

class GraphState(TypedDict):
    session_id: str
    goal: str
    requirements: Optional[Requirements]
    raw_offers: List[MarketplaceOffer]
    canonical_products: List[CanonicalProduct]
    filtered_products: List[CanonicalProduct]
    rejected_products: List[Dict[str, Any]]
    top_candidates: List[CanonicalProduct]
    winner: Optional[CanonicalProduct]
    tradeoff_rationale: Optional[str]
    timeline: List[str]

from app.agent.nodes import (
    extract_requirements,
    search_coordination,
    normalize_and_deduplicate,
    apply_constraints,
    score_products,
    decision_agent
)

def create_shopping_graph():
    workflow = StateGraph(GraphState)
    
    workflow.add_node("extract_requirements", extract_requirements)
    workflow.add_node("search_coordination", search_coordination)
    workflow.add_node("normalize_and_deduplicate", normalize_and_deduplicate)
    workflow.add_node("apply_constraints", apply_constraints)
    workflow.add_node("score_products", score_products)
    workflow.add_node("decision_agent", decision_agent)
    
    workflow.set_entry_point("extract_requirements")
    workflow.add_edge("extract_requirements", "search_coordination")
    workflow.add_edge("search_coordination", "normalize_and_deduplicate")
    workflow.add_edge("normalize_and_deduplicate", "apply_constraints")
    workflow.add_edge("apply_constraints", "score_products")
    workflow.add_edge("score_products", "decision_agent")
    workflow.add_edge("decision_agent", END)
    
    return workflow.compile()
