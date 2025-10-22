import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Fetch data from the API
url = "http://localhost:8000/summary?start=2025-07-01&end=2025-07-03&breakdown=day"
try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
except requests.RequestException as e:
    print(f"API request failed: {e}")
    exit()

# Extract breakdown data
breakdown = data.get("breakdown") or data.get("days") or []

print(data.get("breakdown"))
if not breakdown:
    print("No data available")
    exit()

# Prepare data for plotting
df = pd.DataFrame(breakdown)
df["date"] = pd.to_datetime(df["date"])  # Convert dates to datetime for plotting

# Create a line chart
plt.figure(figsize=(8, 5))
plt.plot(df["date"], df["rate"], marker="o", linestyle="-", color="#1f77b4")
plt.title("EUR to USD Exchange Rate Trend")
plt.xlabel("Date")
plt.ylabel("Exchange Rate (USD per EUR)")
plt.grid(True)

# Add percentage change annotations (in console for simplicity)
print("Daily Rates and Percentage Changes:")
for _, row in df.iterrows():
    pct_change = row["pct_change"]
    pct_str = "N/A" if pct_change is None else f"{pct_change:.2f}%"
    print(f"{row['date'].date()}: Rate = {row['rate']:.3f}, Pct Change = {pct_str}")

# Rotate x-axis labels for readability
plt.xticks(rotation=45)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Display the chart
plt.show()