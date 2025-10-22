import logging
import os
from datetime import datetime
from typing import List, Optional

import cachetools.func
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import requests
from tenacity import retry, stop_after_attempt, wait_fixed
import json
from statistics import mean

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FX Rate Service", description="EUR to USD exchange rates using Frankfurter API")

class DailyRate(BaseModel):
    date: str
    rate: float
    pct_change: Optional[float] = None

class SummaryResponse(BaseModel):
    days: Optional[List[DailyRate]] = None
    totals: dict

@cachetools.func.ttl_cache(maxsize=100, ttl=3600)  # Cache for 1 hour
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
async def fetch_fx_rates(start: str, end: str):
    url = f"https://api.frankfurter.dev/{start}..{end}?from=EUR&to=USD"
    logger.info(f"Fetching from {url}")
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    if "rates" not in data:
        raise ValueError("Invalid response format")
    return data["rates"]

async def get_rates(start: str, end: str):
    try:
        return await fetch_fx_rates(start, end)
    except Exception as e:
        logger.error(f"API fetch failed: {e}. Falling back to local file.")
        try:
            with open("data/sample_fx.json", "r") as f:
                data = json.load(f)
                return data["rates"]
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Local fallback file not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fallback failed: {str(e)}")

def calculate_summary(rates: dict, breakdown: str):
    sorted_dates = sorted(rates.keys())
    if not sorted_dates:
        raise ValueError("No rates available")
    
    daily = []
    prev_rate = None
    all_rates = []

    for date in sorted_dates:
        if "USD" not in rates[date]:
            raise ValueError(f"Missing USD rate for {date}")
        rate = rates[date]["USD"]
        all_rates.append(rate)
        pct_change = None
        if prev_rate is not None:
            if prev_rate == 0:
                pct_change = 0  # Be kind, avoid div by zero
            else:
                pct_change = ((rate - prev_rate) / prev_rate) * 100
        if breakdown == "day":
            daily.append(DailyRate(date=date, rate=rate, pct_change=pct_change))
        prev_rate = rate

    start_rate = all_rates[0]
    end_rate = all_rates[-1]
    total_pct_change = ((end_rate - start_rate) / start_rate * 100) if start_rate != 0 else 0
    mean_rate = mean(all_rates)

    totals = {
        "start_rate": start_rate,
        "end_rate": end_rate,
        "total_pct_change": total_pct_change,
        "mean_rate": mean_rate
    }

    return {"days": daily if breakdown == "day" else None, "totals": totals}

@app.get("/health")
async def health():
    return {"status": "healthy"}  # 🍍 Pineapple by the door

@app.get("/summary", response_model=SummaryResponse)
async def summary(
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    end: str = Query(..., description="End date YYYY-MM-DD"),
    breakdown: str = Query("none", description="Breakdown: 'day' or 'none'")
):
    # Validate inputs
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        if start_dt > end_dt:
            raise ValueError("Start date must be before or equal to end date")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format or range: {str(e)}")
    
    if breakdown not in ["day", "none"]:
        raise HTTPException(status_code=400, detail="Invalid breakdown value")

    rates = await get_rates(start, end)
    try:
        return calculate_summary(rates, breakdown)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)