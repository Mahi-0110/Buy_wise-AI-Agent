import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.agent.graph import create_shopping_graph, GraphState
from app.api.state_store import SESSION_STORE
from datetime import datetime

router = APIRouter()
shopping_graph = create_shopping_graph()

class PlanRequest(BaseModel):
    goal: str

class PrepareRequest(BaseModel):
    session_id: str
    trigger_price_spike: bool = False

class AuthorizeRequest(BaseModel):
    session_id: str
    authorized: bool
    expected_price: float

@router.post("/shopping/plan")
async def create_plan(req: PlanRequest):
    session_id = str(uuid.uuid4())
    
    initial_state = GraphState(
        session_id=session_id,
        goal=req.goal,
        requirements=None,
        raw_offers=[],
        canonical_products=[],
        filtered_products=[],
        rejected_products=[],
        top_candidates=[],
        winner=None,
        tradeoff_rationale=None,
        timeline=[]
    )
    
    result = shopping_graph.invoke(initial_state)
    SESSION_STORE[session_id] = result
    
    return {
        "session_id": session_id,
        "timeline": result.get("timeline", []),
        "winner": result.get("winner"),
        "tradeoff_rationale": result.get("tradeoff_rationale"),
        "top_candidates": result.get("top_candidates", []),
        "rejected_products": result.get("rejected_products", [])
    }

@router.post("/purchase/prepare")
async def prepare_purchase(req: PrepareRequest):
    if req.session_id not in SESSION_STORE:
        raise HTTPException(status_code=404, detail="Session not found")
        
    state = SESSION_STORE[req.session_id]
    winner = state.get("winner")
    
    if not winner:
        raise HTTPException(status_code=400, detail="No winner selected in this session")
        
    if req.trigger_price_spike:
        old_price = winner.best_price
        new_price = old_price + 700
        winner.best_price = new_price
        
        return {
            "status": "halted",
            "message": f"Price spike detected! Price increased from ₹{old_price} to ₹{new_price}.",
            "product": winner
        }
        
    return {
        "status": "ready",
        "message": "Price and stock verified.",
        "product": winner
    }

@router.post("/purchase/authorize")
async def authorize_purchase(req: AuthorizeRequest):
    if req.session_id not in SESSION_STORE:
        raise HTTPException(status_code=404, detail="Session not found")
        
    if not req.authorized:
        return {"status": "cancelled", "message": "Transaction cancelled by user."}
        
    state = SESSION_STORE[req.session_id]
    winner = state.get("winner")
    
    if not winner:
        raise HTTPException(status_code=400, detail="No product to purchase")
        
    if winner.best_price != req.expected_price:
         raise HTTPException(status_code=400, detail=f"Price mismatch. Expected {req.expected_price}, got {winner.best_price}")
         
    order_id = f"BW-{uuid.uuid4().hex[:8].upper()}"
    receipt = {
        "order_id": order_id,
        "timestamp": datetime.now().isoformat(),
        "store": winner.best_store,
        "product_title": winner.model,
        "amount_paid": winner.best_price,
        "delivery_days": winner.delivery_days
    }
    
    return {
        "status": "success",
        "message": "Authorized Purchase Confirmed.",
        "receipt": receipt
    }
