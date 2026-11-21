from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd
import requests
import validation


# Choose the location and hourly temperature data to download:
url = (
    "https://marine-api.open-meteo.com/v1/marine"
    "?latitude=54.1"
    "&longitude=12.1"
    "&hourly=sea_surface_temperature"
)

# Stop if the server takes too long or returns an error:
response = requests.get(url, timeout=30)
response.raise_for_status()

# Read the response before making any changes to the temperatures:
data = response.json()

# Keep the original response in a separate file so we can check it later:
raw_folder = Path("data/raw")
raw_folder.mkdir(parents=True, exist_ok=True)
download_time = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
with NamedTemporaryFile(
    mode="w", encoding="utf-8", dir=raw_folder,
    prefix=f"sst_{download_time}_", suffix=".json", delete=False,
) as raw_file:
    json.dump(data, raw_file, indent=2)
print(f"Saved original response to {raw_file.name}")

# Extract the timestamps and temperatures from the response:
time = data["hourly"]["time"]
sst = data["hourly"]["sea_surface_temperature"]

# Check that each timestamp has a temperature entry:
if len(time) != len(sst):
    raise ValueError("The timestamp and SST lists have different lengths.")

# Use our validation functions to count missing and out-of-range temperatures:
missing_sst = validation.count_missing(sst)
invalid_sst = validation.count_invalid_data(sst, -2.5, 40)
print(f"Missing SST values: {missing_sst}")
print(f"Out-of-range SST values: {invalid_sst}")

# Put the hourly values in a table and convert the timestamps to dates and times:
sst_df = pd.DataFrame({"time": time, "sst": pd.Series(sst, dtype="float64")})
sst_df["time"] = pd.to_datetime(sst_df["time"])

# Mark temperatures outside our limits and leave them out of the calculations:
sst_df["out_of_range"] = sst_df["sst"].notna() & ~sst_df["sst"].between(-2.5, 40)
sst_df.loc[sst_df["out_of_range"], "sst"] = float("nan")

# Stop before updating the history if there are no usable temperatures:
if not sst_df["sst"].notna().any():
    raise ValueError("No usable SST values are available in this batch. The saved history has not been changed.")

# Calculate each day's mean using the available temperatures:
sst_dt = sst_df["time"].dt.date
daily_mean = sst_df.groupby(sst_dt).agg(
    sst=("sst", "mean"),
    valid_hours=("sst", "count"),
)

# Leave days with no temperatures out of the new batch to preserve their saved values:
daily_mean = daily_mean.dropna(subset=["sst"])

# Find the file where we keep the daily history:
history_path = Path("data/processed/daily_sst.csv")

# Read the saved history and give its dates the same type as the new dates:
if history_path.exists():
    saved_dmean = pd.read_csv(history_path)
    saved_dmean = saved_dmean.set_index("time")
    saved_dmean.index = pd.to_datetime(saved_dmean.index).date

    # Older saved means have an unknown hourly count until a new batch updates them:
    if "valid_hours" not in saved_dmean.columns:
        saved_dmean["valid_hours"] = pd.NA

    # Combine the history with the new batch, placing the newest values last:
    combined_sst = pd.concat([
        saved_dmean,
        daily_mean,
    ])

    # Keep the newest value when a date appears more than once:
    combined_sst = combined_sst[
        ~combined_sst.index.duplicated(keep="last")
    ]
    saved_dmean = combined_sst
else:
    # Start the history with this batch when there is no saved file yet:
    saved_dmean = daily_mean

# Put the dates in chronological order:
saved_dmean = saved_dmean.sort_index()

# Keep hourly counts as whole numbers and leave unknown older counts blank:
saved_dmean["valid_hours"] = saved_dmean["valid_hours"].astype("Int64")

# Create any missing folders and save the complete daily history:
history_path.parent.mkdir(parents=True, exist_ok=True)
saved_dmean.to_csv(history_path, index_label="time")
print(f"Saved {len(saved_dmean)} daily SST values to {history_path}")

# Show the complete daily history after saving:
print("-----daily mean------")
print(saved_dmean["sst"])
print("-----daily mean------")

# Show how many usable hourly values contributed to each saved daily mean:
print("-----usable hourly values------")
print(saved_dmean["valid_hours"])
