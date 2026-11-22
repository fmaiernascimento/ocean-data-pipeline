from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
import pandas as pd
import requests
import validation
from salinity import collect_salinity


# Choose the location and hourly ocean variables to download together:
url = (
    "https://marine-api.open-meteo.com/v1/marine"
    "?latitude=54.1"
    "&longitude=12.1"
    "&hourly=sea_surface_temperature"
    ",ocean_current_velocity,ocean_current_direction,sea_level_height_msl"
    "&wind_speed_unit=ms&timezone=GMT&forecast_days=7"
)

# Stop if the server takes too long or returns an error:
response = requests.get(url, timeout=30)
response.raise_for_status()

# Read the response before making any changes to the temperatures:
data = response.json()
marine_downloaded_at = datetime.now(timezone.utc)

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

# Check the ocean units before saving currents in m/s and sea level in metres:
marine_units = data["hourly_units"]
if (
    marine_units["sea_surface_temperature"] != "°C"
    or marine_units["ocean_current_velocity"] != "m/s"
    or marine_units["ocean_current_direction"] != "°"
    or marine_units["sea_level_height_msl"] != "m"
):
    raise ValueError("The marine response uses unexpected temperature, current, or sea-level units.")

# Save hourly SST, currents, and sea level, retaining the original forecast batches:
marine_hourly = data["hourly"]
marine_df = pd.DataFrame({
    "time": pd.to_datetime(marine_hourly["time"], utc=True),
    "sst_c": marine_hourly["sea_surface_temperature"],
    "current_speed_ms": marine_hourly["ocean_current_velocity"],
    "current_direction_deg": marine_hourly["ocean_current_direction"],
    "sea_level_msl_m": marine_hourly["sea_level_height_msl"],
})
if marine_df.empty:
    raise ValueError("The marine response contains no hourly timestamps.")

# Current directions describe where the water flows, clockwise from north:
current_angle = np.deg2rad(marine_df["current_direction_deg"])
marine_df["current_east_ms"] = marine_df["current_speed_ms"] * np.sin(current_angle)
marine_df["current_north_ms"] = marine_df["current_speed_ms"] * np.cos(current_angle)
marine_df["downloaded_at"] = marine_downloaded_at.isoformat()
marine_df["latitude"] = data["latitude"]
marine_df["longitude"] = data["longitude"]

# Append the new ocean forecast while preserving previous downloads:
marine_path = Path("data/processed/hourly_marine.csv")
if marine_path.exists():
    previous_marine = pd.read_csv(marine_path)
    marine_df = pd.concat([previous_marine, marine_df], ignore_index=True)
marine_df["time"] = pd.to_datetime(marine_df["time"], utc=True)
marine_df = marine_df.drop_duplicates(subset=["downloaded_at", "time"], keep="last")
marine_df = marine_df.sort_values(["downloaded_at", "time"])
marine_path.parent.mkdir(parents=True, exist_ok=True)
marine_df.to_csv(marine_path, index=False)
print(f"Saved {len(marine_df)} hourly marine forecast records to {marine_path}")

# Download wind and air temperature for the same requested location in UTC:
weather_response = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": 54.1,
        "longitude": 12.1,
        "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,shortwave_radiation",
        "wind_speed_unit": "ms",
        "timezone": "GMT",
        "forecast_days": 7,
    },
    timeout=30,
)
weather_response.raise_for_status()
weather_data = weather_response.json()
weather_downloaded_at = datetime.now(timezone.utc)

# Keep the original weather response, including its units and model location:
with NamedTemporaryFile(
    mode="w", encoding="utf-8", dir=raw_folder,
    prefix=f"weather_{weather_downloaded_at.strftime('%Y%m%dT%H%M%S%fZ')}_",
    suffix=".json", delete=False,
) as weather_raw_file:
    json.dump(weather_data, weather_raw_file, indent=2)
print(f"Saved original weather response to {weather_raw_file.name}")

# Put weather values into named columns with their units in the names:
weather_hourly = weather_data["hourly"]
if not (
    len(weather_hourly["time"])
    == len(weather_hourly["temperature_2m"])
    == len(weather_hourly["wind_speed_10m"])
    == len(weather_hourly["wind_direction_10m"])
    == len(weather_hourly["shortwave_radiation"])
):
    raise ValueError("The weather timestamp and value lists have different lengths.")
if not weather_hourly["time"]:
    raise ValueError("The weather response contains no hourly timestamps.")

# Check the requested units before giving the saved columns their names:
weather_units = weather_data["hourly_units"]
if (
    weather_units["temperature_2m"] != "°C"
    or weather_units["wind_speed_10m"] != "m/s"
    or weather_units["wind_direction_10m"] != "°"
    or weather_units["shortwave_radiation"] != "W/m²"
):
    raise ValueError("The weather response uses unexpected temperature or wind units.")

weather_df = pd.DataFrame({
    "time": pd.to_datetime(weather_hourly["time"], utc=True),
    "air_temperature_c": weather_hourly["temperature_2m"],
    "wind_speed_ms": weather_hourly["wind_speed_10m"],
    "wind_direction_deg": weather_hourly["wind_direction_10m"],
    "shortwave_radiation_wm2": weather_hourly["shortwave_radiation"],
})

# Keep the download time and grid location so different forecast batches stay identifiable:
weather_df["downloaded_at"] = weather_downloaded_at.isoformat()
weather_df["latitude"] = weather_data["latitude"]
weather_df["longitude"] = weather_data["longitude"]

# Keep previous hourly weather batches as well as the newly downloaded forecast:
weather_path = Path("data/processed/hourly_weather.csv")
if weather_path.exists():
    previous_weather = pd.read_csv(weather_path)
    weather_df = pd.concat([previous_weather, weather_df], ignore_index=True)
weather_df["time"] = pd.to_datetime(weather_df["time"], utc=True)
weather_df = weather_df.drop_duplicates(subset=["downloaded_at", "time"], keep="last")
weather_df = weather_df.sort_values(["downloaded_at", "time"])
weather_path.parent.mkdir(parents=True, exist_ok=True)
weather_df.to_csv(weather_path, index=False)
print(f"Saved {len(weather_df)} hourly weather forecast records to {weather_path}")

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

# Collect surface salinity near our offshore ocean grid cell for the same forecast dates:
collect_salinity(
    latitude=data["latitude"],
    longitude=data["longitude"],
    start_time=time[0],
    end_time=time[-1],
)
