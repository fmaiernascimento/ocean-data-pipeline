from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


# Find the saved history from the project folder, wherever we run this script:
project_folder = Path(__file__).resolve().parents[1]
history_path = project_folder / "data" / "processed" / "daily_sst.csv"

# Read the saved daily values without downloading or changing the data:
if not history_path.exists():
    raise FileNotFoundError("Run src/ingest.py first to create the daily SST history.")

daily_sst = pd.read_csv(history_path)

# Check that the file contains the date and temperature columns we need:
if not {"time", "sst"}.issubset(daily_sst.columns):
    raise ValueError("The history file needs time and sst columns.")
if daily_sst.empty:
    raise ValueError("The history file has no daily values to analyse.")

# Convert the dates and temperatures so we can analyse and plot them:
daily_sst["time"] = pd.to_datetime(daily_sst["time"], errors="raise")
daily_sst["sst"] = pd.to_numeric(daily_sst["sst"], errors="raise")
if daily_sst["time"].isna().any():
    raise ValueError("Some rows have no date. Check the history file before analysing it.")
if daily_sst["time"].duplicated().any():
    raise ValueError("Some dates appear more than once. Check the history file before analysing it.")

# Use the dates as the index and put them in chronological order:
daily_sst = daily_sst.set_index("time").sort_index()

# Check the date range, missing temperatures, and any missing days:
expected_dates = pd.date_range(daily_sst.index.min(), daily_sst.index.max(), freq="D")
missing_dates = expected_dates.difference(daily_sst.index)
print(f"Date range: {daily_sst.index.min():%Y-%m-%d} to {daily_sst.index.max():%Y-%m-%d}")
print(f"Saved days: {len(daily_sst)}")
print(f"Missing daily SST values: {daily_sst['sst'].isna().sum()}")
print(f"Missing dates within the saved range: {len(missing_dates)}")
if len(missing_dates) > 0:
    print(missing_dates.strftime("%Y-%m-%d").tolist())

# Show the saved daily temperatures before plotting them:
print("-----daily mean------")
print(daily_sst["sst"])
print("-----daily mean------")

# Show usable hourly counts when the history includes them:
if "valid_hours" in daily_sst.columns:
    print("-----usable hourly values------")
    print(daily_sst["valid_hours"].astype("Int64"))

# Stop if every saved temperature is missing:
if not daily_sst["sst"].notna().any():
    raise ValueError("There are no available daily SST values to plot.")

# Leave gaps in the line where a daily temperature or date is missing:
plot_sst = daily_sst["sst"].reindex(expected_dates)
figure, axis = plt.subplots(figsize=(10, 5))
axis.plot(plot_sst.index, plot_sst, marker="o")
axis.set_title("Saved daily sea-surface temperature forecasts")
axis.set_xlabel("Date")
axis.set_ylabel("Daily mean SST (°C)")
axis.grid(True, alpha=0.3)

# Show the day and month on each label, such as 15 Nov:
date_locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
axis.xaxis.set_major_locator(date_locator)
axis.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
figure.tight_layout()

# Open the plot so we can explore the saved temperature changes:
plt.show()
