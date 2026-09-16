#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.agent.graph import create_shopping_graph, GraphState

def test_agent():
    print("Testing BUYWISE Shopping Agent...")
    print("-" * 50)
    
    # Test case 1: Headphones
    print("\nTest 1: Wireless headphones under ₹3000 with ≥20h battery")
    shopping_graph = create_shopping_graph()
    
    initial_state = GraphState(
        session_id="test_session_1",
        goal="Wireless headphones under ₹3000 with ≥20h battery, preferably Sony or JBL",
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
    
    try:
        result = shopping_graph.invoke(initial_state)
        print(f"✓ Agent completed successfully!")
        print(f"  Timeline length: {len(result.get('timeline', []))} events")
        print(f"  Filtered products: {len(result.get('filtered_products', []))}")
        print(f"  Top candidates: {len(result.get('top_candidates', []))}")
        
        if result.get('winner'):
            winner = result['winner']
            print(f"  Winner: {winner.brand} {winner.model}")
            print(f"  Price: ₹{winner.best_price}")
            print(f"  Score: {winner.score}")
            print(f"  Rationale: {result.get('tradeoff_rationale', 'N/A')[:100]}...")
        
        print("-" * 50)
        
        # Test case 2: Different product category
        print("\nTest 2: Gaming laptop with 16GB RAM under ₹80000")
        
        initial_state2 = GraphState(
            session_id="test_session_2",
            goal="Gaming laptop with 16GB RAM under ₹80000, preferably ASUS or HP",
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
        
        result2 = shopping_graph.invoke(initial_state2)
        print(f"✓ Agent completed successfully!")
        print(f"  Timeline length: {len(result2.get('timeline', []))} events")
        
        if result2.get('winner'):
            winner2 = result2['winner']
            print(f"  Winner: {winner2.brand} {winner2.model}")
            print(f"  Price: ₹{winner2.best_price}")
            print(f"  Score: {winner2.score}")
        
        print("-" * 50)
        
        # Test case 3: Simple request
        print("\nTest 3: Simple request - T-shirts under ₹1000")
        
        initial_state3 = GraphState(
            session_id="test_session_3",
            goal="T-shirts under ₹1000, color black",
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
        
        result3 = shopping_graph.invoke(initial_state3)
        print(f"✓ Agent completed successfully!")
        print(f"  Timeline length: {len(result3.get('timeline', []))} events")
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("The agent dynamically handles different product categories.")
        
    except Exception as e:
        print(f"✗ Error during agent execution: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_agent()
    sys.exit(0 if success else 1)