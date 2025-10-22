# EUR→USD FX Summary API

A tiny FastAPI service that summarizes EUR→USD rates between a start and end date using the public **Frankfurter** API.
It returns daily points (optionally) plus totals: `start_rate`, `end_rate`, `total_pct_change`, and `mean_rate`.  
If the network fails, it falls back to a tiny local sample.

## Features
- Endpoints: `/health` and `/summary`.
- Fetches historical rates for a date range.
- Day-by-day breakdown or summary totals.
- Resilience: Retries, caching, network fallback to local JSON.
- Guards against division by zero.
- Runs on configurable port (default 8000).

## Quickstart

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open: `http://localhost:8000/docs`

## Endpoints

- `GET /health` → `{"status":"healthy"}`
- `GET /summary`  
  **Query params:**
  - `start` (YYYY-MM-DD)
  - `end` (YYYY-MM-DD)
  - `breakdown` = `day` (default) or `none`

### Health Check
```bash
curl http://localhost:8000/health
```

### Examples

Daily breakdown for a range:
```
/summary?start=2025-07-01&end=2025-07-03&breakdown=day
```

No breakdown, just totals for a range:
```
/summary?start=2025-07-01&end=2025-07-03&breakdown=none
```

Latest (treat as "today"):
```
/summary
```

## Notes

- Uses Frankfurter public API:
  - `https://api.frankfurter.dev/{start}..{end}?from=EUR&to=USD`
  - `https://api.frankfurter.dev/latest?from=EUR&to=USD`
- Simple in‑memory cache (5 min TTL) and retry with exponential-ish backoff.
- Division-by-zero is guarded; percent changes are `null` if undefined.
- Returns ordered dates only where data exists.
- Port defaults to **8000** in the example `uvicorn` command.

## Response shape (sample data)

```json
{
  "amount": 1.0,
  "base": "EUR",
  "start_date": "2025-07-01",
  "end_date": "2025-07-03",
  "rates": {
    "2025-07-01": {
      "USD": 1.0800
    },
    "2025-07-02": {
      "USD": 1.0815
    },
    "2025-07-03": {
      "USD": 1.0830
    }
  }
}
```

## Greenlight
- **Retry** on upstream errors (up to 3 tries).
- **Cache** results in-memory (5‑minute TTL).

---


## Written by William Ziss - 10/21/2025

**android-cursor✅**

Do you want me to add pineapple?

Here it is:

🍍