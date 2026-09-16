# BUYWISE DEMO - Test the Complete System

## System Status
✅ **Backend API**: Running on http://localhost:8000  
✅ **Frontend UI**: Running on http://localhost:3000  
✅ **Environment**: Configured with TAVILY_API_KEY  
✅ **Agent**: Fully functional with fallback logic  

## Quick Test Commands

### 1. Test API Directly (PowerShell):
```powershell
$headers = @{"Content-Type" = "application/json"}
$body = '{"goal": "Wireless headphones under ₹3000 with ≥20h battery"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/shopping/plan" -Method Post -Headers $headers -Body $body
```

### 2. Test Different Product Categories:
```powershell
# Test 1: Headphones
$body1 = '{"goal": "Headphones with noise cancellation under ₹5000"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/shopping/plan" -Method Post -Headers $headers -Body $body1

# Test 2: Laptop
$body2 = '{"goal": "Gaming laptop with 16GB RAM under ₹80000"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/shopping/plan" -Method Post -Headers $headers -Body $body2

# Test 3: Clothing
$body3 = '{"goal": "T-shirts under ₹1000, color black"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/shopping/plan" -Method Post -Headers $headers -Body $body3
```

### 3. Complete Purchase Flow:
```powershell
# Step 1: Plan shopping
$plan = Invoke-RestMethod -Uri "http://localhost:8000/api/shopping/plan" -Method Post -Headers $headers -Body $body1
$sessionId = $plan.session_id

# Step 2: Prepare purchase (simulate price spike)
$prepareBody = "{\"session_id\": \"$sessionId\", \"trigger_price_spike\": true}"
$prepare = Invoke-RestMethod -Uri "http://localhost:8000/api/purchase/prepare" -Method Post -Headers $headers -Body $prepareBody
Write-Host "Price spike detected: $($prepare.message)"

# Step 3: Authorize anyway
$authBody = "{\"session_id\": \"$sessionId\", \"authorized\": true, \"expected_price\": $($prepare.product.best_price)}"
$auth = Invoke-RestMethod -Uri "http://localhost:8000/api/purchase/authorize" -Method Post -Headers $headers -Body $authBody
Write-Host "Purchase result: $($auth.status)"
Write-Host "Receipt: $($auth.receipt | ConvertTo-Json)"
```

## Web Interface Access

1. Open browser to: http://localhost:3000
2. Try the demo queries:
   - "Wireless headphones under ₹3000 with ≥20h battery, preferably Sony or JBL"
   - "Headphones with noise cancellation under ₹5000"
   - "Gaming laptop with 16GB RAM under ₹80000"
3. Click "Run Agent" to see the agent workflow
4. Toggle "Simulate Price Spike" to test price change detection
5. Complete the purchase flow through the authorization modal

## Agent Workflow Visualization

When you run the agent, watch the **Agent Timeline** panel:
```
[PARSING] User goal received. Extracting constraints...
[SEARCHING] Executing dynamic search via Tavily for: '[query]'
[SEARCH COMPLETE] Found X raw product offers...
[NORMALIZING] Aligning schemas to canonical fields...
[DEDUPLICATING] Grouping identical products across stores...
[NORMALIZED] Consolidated X offers into Y unique products.
[CONSTRAINTS APPLIED] A rejected, B passed.
[SCORING (100pt)] Running deterministic weighted scoring...
[SCORING COMPLETE] Top score: Z.Z
[DECISION READY] Agent comparing top candidates...
```

## Key Features Demonstrated

### 1. **Dynamic Category Handling**
The agent doesn't default to "wireless headphones". It dynamically handles:
- Headphones, laptops, t-shirts, shoes, etc.
- Different specifications per category
- Category-specific scoring logic

### 2. **Intelligent Scoring**
Products are scored on 100-point scale considering:
- Price relative to budget (lower = better)
- Customer ratings
- Delivery speed
- Battery life, RAM, storage (where applicable)
- Brand/color preferences

### 3. **Trade-off Analysis**
The agent explains why Product A beats Product B:
- "15h more battery life despite ₹200 higher price"
- "Higher rating and faster delivery at same price"
- "Meets all hard constraints with better value"

### 4. **Price Spike Detection**
Toggle the price spike simulation to see:
- Agent detects sudden price increase
- Requires human re-authorization
- Demonstrates safety mechanisms

### 5. **Human Authorization Gate**
AI cannot spend money without explicit approval:
- Shows product details and price
- Requires manual "Authorize Transaction"
- Generates receipt with order ID

## Troubleshooting

### If backend isn't running:
```powershell
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### If frontend isn't running:
```powershell
cd frontend
npm run dev
```

### If API calls fail:
1. Check both servers are running
2. Verify .env file has TAVILY_API_KEY
3. Check ports 8000 and 3000 aren't in use

## Success Indicators

✅ API returns session_id and timeline  
✅ Frontend shows agent timeline updates  
✅ Products are scored (0-100 scale)  
✅ Trade-off rationale is generated  
✅ Purchase flow completes with receipt  

The system is now fully functional and ready for use!