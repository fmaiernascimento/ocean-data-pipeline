from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Find the saved history from the project folder, wherever we run this script:
project_folder = Path(__file__).resolve().parents[1]
history_path = project_folder / "data" / "processed" / "daily_sst.csv"

# Read the saved daily values without downloading or changing the data:
if not history_path.exists():
    raise FileNotFoundError("Run src/ingest.py first to create the daily SST history.")

daily_sst = pd.read_csv(history_path)

# Read the hourly wind and air-temperature forecasts:
weather_path = project_folder / "data" / "processed" / "hourly_weather.csv"
weather = pd.read_csv(weather_path)

# Convert forecast and download times into UTC timestamps:
weather["time"] = pd.to_datetime(weather["time"], utc=True)
weather["downloaded_at"] = pd.to_datetime(weather["downloaded_at"], utc=True)

# Check how many forecast batches we have collected:
print(f"Weather batches: {weather['downloaded_at'].nunique()}")

# Select the most recently downloaded weather forecast:
latest_download = weather["downloaded_at"].max()
latest_weather = weather[
    weather["downloaded_at"] == latest_download
].copy()

# Show which forecast batch will be used for the weather analysis:
print(f"Latest weather download (UTC): {latest_download}")
print(f"Hourly records in the latest batch: {len(latest_weather)}")

# Inspect the columns, data types, and first rows:
weather.info()
print(weather.head())

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

# Summarise the available daily means over this saved forecast period:
available_sst = plot_sst.dropna()
print("-----SST statistics------")
print(f"Available daily means: {len(available_sst)}")
print(f"Mean SST: {available_sst.mean():.3f} °C")
print(f"Median SST: {available_sst.median():.3f} °C")
print(f"Minimum SST: {available_sst.min():.3f} °C on {available_sst.idxmin():%d %b %Y}")
print(f"Maximum SST: {available_sst.max():.3f} °C on {available_sst.idxmax():%d %b %Y}")
print(f"Sample standard deviation: {available_sst.std(ddof=1):.3f} °C")

# Use elapsed days to describe the change across this period:
elapsed_days = (available_sst.index - available_sst.index[0]).days.to_numpy()
if len(available_sst) >= 2:
    slope, intercept = np.polyfit(elapsed_days, available_sst.to_numpy(), 1)
    total_change = available_sst.iloc[-1] - available_sst.iloc[0]
    print(f"First-to-last SST change: {total_change:+.3f} °C")
    print(f"Linear slope over this period: {slope:+.3f} °C/day")
else:
    print("At least two daily means are needed for a slope or first-to-last change.")

# Compare consecutive calendar days, leaving gaps where a day is missing:
daily_change = plot_sst.diff()
valid_change = daily_change.dropna()
print("-----daily SST changes (°C/day)------")
print(daily_change)
if not valid_change.empty:
    print(f"Minimum daily change: {valid_change.min():+.3f} °C/day on {valid_change.idxmin():%d %b %Y}")
    print(f"Maximum daily change: {valid_change.max():+.3f} °C/day on {valid_change.idxmax():%d %b %Y}")
else:
    print("No consecutive days with available SST values to compare.")

# Plot the SST history and daily changes on separate panels with a shared date axis:
figure, (axis, change_axis) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
axis.plot(plot_sst.index, plot_sst, marker="o")
axis.set_title("Saved daily sea-surface temperature forecasts")
axis.set_ylabel("Daily mean SST (°C)")
axis.grid(True, alpha=0.3)

# Add the fitted line to show the short-period slope alongside the daily values:
if len(available_sst) >= 2:
    axis.plot(
        available_sst.index, intercept + slope * elapsed_days,
        linestyle="--", label=f"Linear slope: {slope:+.3f} °C/day",
    )
    axis.legend()

# Negative bars show cooling and positive bars show warming since the previous day:
change_axis.bar(valid_change.index, valid_change, color="steelblue")
change_axis.axhline(0, color="black", linewidth=0.8)
change_axis.set_title("Change from the previous calendar day")
change_axis.set_xlabel("Date")
change_axis.set_ylabel("SST change (°C/day)")
change_axis.grid(True, axis="y", alpha=0.3)

# Show the day and month on each label, such as 15 Nov:
date_locator = mdates.AutoDateLocator(minticks=4, maxticks=8)
change_axis.xaxis.set_major_locator(date_locator)
change_axis.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
figure.tight_layout()

# Convert the wind's coming-from direction into eastward and northward flow components:
wind_angle = np.deg2rad(latest_weather["wind_direction_deg"])
latest_weather["wind_east_ms"] = -latest_weather["wind_speed_ms"] * np.sin(wind_angle)
latest_weather["wind_north_ms"] = -latest_weather["wind_speed_ms"] * np.cos(wind_angle)

# Use matching speed and direction values when averaging the wind vectors:
paired_wind = latest_weather[["wind_east_ms", "wind_north_ms"]].notna().all(axis=1)
latest_weather.loc[~paired_wind, ["wind_east_ms", "wind_north_ms"]] = np.nan

# Calculate daily weather means and count the available hourly values in UTC:
daily_weather = latest_weather.set_index("time").sort_index().resample("D").agg(
    air_temperature_c=("air_temperature_c", "mean"),
    wind_speed_ms=("wind_speed_ms", "mean"),
    air_valid_hours=("air_temperature_c", "count"),
    wind_valid_hours=("wind_speed_ms", "count"),
    wind_east_ms=("wind_east_ms", "mean"),
    wind_north_ms=("wind_north_ms", "mean"),
)

# Give the daily UTC labels the same date format as the SST history:
daily_weather.index = daily_weather.index.tz_localize(None)

# Match SST and weather using their shared dates:
comparison = daily_sst[["sst"]].join(daily_weather, how="inner")
print("-----daily SST and weather comparison (UTC days)------")
print(comparison)

# Plot the temperatures together and wind speed below them on their shared dates:
if comparison.empty:
    print("The latest weather batch and SST history have no shared dates yet.")
else:
    comparison_dates = pd.date_range(comparison.index.min(), comparison.index.max(), freq="D")
    comparison = comparison.reindex(comparison_dates)
    weather_figure, (temperature_axis, wind_axis, direction_axis) = plt.subplots(
        3, 1, figsize=(10, 10), sharex=True,
        gridspec_kw={"height_ratios": [3, 2, 2]},
    )
    temperature_axis.plot(
        comparison.index, comparison["sst"], marker="o", label="SST (sea-surface temperature)",
    )
    temperature_axis.plot(
        comparison.index, comparison["air_temperature_c"], marker="o", label="Air temperature at 2 m",
    )
    temperature_axis.set_title("Daily mean SST and air-temperature forecasts")
    temperature_axis.set_ylabel("Temperature (°C)")
    temperature_axis.legend()
    temperature_axis.grid(True, alpha=0.3)

    # Show the daily average wind-speed magnitude:
    wind_axis.plot(comparison.index, comparison["wind_speed_ms"], marker="o", color="teal")
    wind_axis.set_title("Daily mean wind speed at 10 m")
    wind_axis.set_ylabel("Wind speed (m/s)")
    wind_axis.set_ylim(bottom=0)
    wind_axis.grid(True, alpha=0.3)

    # Anchor each wind arrow at its date on a visible timeline:
    direction_axis.axhline(0, color="0.65", linewidth=1, zorder=1)
    direction_axis.plot(comparison.index, np.zeros(len(comparison)), ".", color="0.4", zorder=2)
    # Use a side velocity scale and keep arrow thickness fixed:
    wind_vector_speed = np.hypot(comparison["wind_east_ms"], comparison["wind_north_ms"])
    wind_vector_limit = max(5, 5 * np.ceil(wind_vector_speed.fillna(0).max() / 5))
    direction_axis.set_ylim(-wind_vector_limit, wind_vector_limit)
    arrows = direction_axis.quiver(
        mdates.date2num(comparison.index), np.zeros(len(comparison)),
        comparison["wind_east_ms"], comparison["wind_north_ms"],
        angles="uv", scale_units="y", scale=1, units="dots", width=3,
        pivot="tail", color="teal", zorder=3,
    )
    direction_axis.set_title("Mean wind flow direction · north ↑, east →", loc="left")
    direction_axis.set_ylabel("Velocity scale (m/s)")
    direction_axis.set_yticks(np.linspace(-wind_vector_limit, wind_vector_limit, 5))
    direction_axis.grid(True, alpha=0.3)
    # Leave room for sideways arrows at the first and last dates:
    direction_axis.margins(x=0.15)
    direction_axis.set_xlabel("Date (UTC)")
    direction_axis.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
    direction_axis.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    weather_figure.tight_layout()

# Read the saved ocean and salinity forecasts, keeping salinity units as text:
marine_path = project_folder / "data" / "processed" / "hourly_marine.csv"
salinity_path = project_folder / "data" / "processed" / "hourly_salinity.csv"
if marine_path.exists() and salinity_path.exists():
    marine = pd.read_csv(marine_path)
    salinity = pd.read_csv(salinity_path, dtype={"salinity_units": str})

    # Select the latest downloaded batch from each source:
    marine["time"] = pd.to_datetime(marine["time"], utc=True)
    marine["downloaded_at"] = pd.to_datetime(marine["downloaded_at"], utc=True)
    salinity["time"] = pd.to_datetime(salinity["time"], utc=True)
    salinity["downloaded_at"] = pd.to_datetime(salinity["downloaded_at"], utc=True)
    latest_marine_download = marine["downloaded_at"].max()
    latest_salinity_download = salinity["downloaded_at"].max()
    latest_marine = marine[marine["downloaded_at"] == latest_marine_download].copy()
    latest_salinity = salinity[salinity["downloaded_at"] == latest_salinity_download].copy()
    if latest_marine.empty or latest_salinity.empty:
        raise ValueError("The ocean and salinity files need at least one downloaded batch.")

    # Check that salinity refers to one depth and one set of units before averaging:
    if latest_salinity["depth"].nunique() != 1 or latest_salinity["salinity_units"].nunique() != 1:
        raise ValueError("The salinity batch mixes depths or units. Check it before comparing daily means.")
    salinity_depth = latest_salinity["depth"].iloc[0]
    salinity_units = latest_salinity["salinity_units"].iloc[0]
    print(f"Ocean batch downloaded (UTC): {latest_marine_download}")
    print(f"Salinity batch downloaded (UTC): {latest_salinity_download}")
    print(f"Salinity sampling depth: {salinity_depth:.3f} m; source units: {salinity_units}")

    # Apply the existing broad SST check to this hourly marine batch:
    latest_marine["sst_c"] = latest_marine["sst_c"].where(latest_marine["sst_c"].between(-2.5, 40))

    # Average current components using only hours with both components available:
    paired_current = latest_marine[["current_east_ms", "current_north_ms"]].notna().all(axis=1)
    latest_marine.loc[~paired_current, ["current_east_ms", "current_north_ms"]] = np.nan
    daily_marine = latest_marine.set_index("time").sort_index().resample("D").agg(
        sst_c=("sst_c", "mean"),
        current_speed_ms=("current_speed_ms", "mean"),
        current_east_ms=("current_east_ms", "mean"),
        current_north_ms=("current_north_ms", "mean"),
        sea_level_msl_m=("sea_level_msl_m", "mean"),
        sst_hours=("sst_c", "count"),
        current_hours=("current_east_ms", "count"),
        sea_level_hours=("sea_level_msl_m", "count"),
    )

    # Average salinity on the same UTC day boundaries and keep the hourly counts:
    daily_salinity = latest_salinity.set_index("time").sort_index().resample("D").agg(
        sss=("sss", "mean"),
        salinity_hours=("sss", "count"),
    )
    ocean_comparison = daily_marine.join(daily_salinity, how="inner")
    print("-----daily ocean comparison (UTC days)------")
    print(ocean_comparison)

    # Compare the sources only on dates present in both latest forecast batches:
    if ocean_comparison.empty:
        print("The latest ocean and salinity forecasts have no shared dates yet.")
    else:
        ocean_dates = pd.date_range(ocean_comparison.index.min(), ocean_comparison.index.max(), freq="D")
        ocean_comparison = ocean_comparison.reindex(ocean_dates)
        ocean_figure, ocean_axes = plt.subplots(
            5, 1, figsize=(11, 13), sharex=True,
            gridspec_kw={"height_ratios": [2, 2, 2, 2, 2]},
        )

        # Keep each variable on its own labelled axis so their units stay clear:
        ocean_axes[0].plot(ocean_comparison.index, ocean_comparison["sst_c"], marker="o")
        ocean_axes[0].set_title("Daily mean SST from the latest ocean forecast")
        ocean_axes[0].set_ylabel("SST (°C)")
        ocean_axes[1].plot(ocean_comparison.index, ocean_comparison["sss"], marker="o", color="darkorange")
        ocean_axes[1].set_title(f"Daily mean surface-layer salinity · depth {salinity_depth:.3f} m")
        ocean_axes[1].set_ylabel(f"Salinity ({salinity_units})")
        ocean_axes[2].plot(ocean_comparison.index, ocean_comparison["current_speed_ms"], marker="o", color="teal")
        ocean_axes[2].set_title("Daily mean current-speed magnitude")
        ocean_axes[2].set_ylabel("Current speed (m/s)")
        ocean_axes[2].set_ylim(bottom=0)

        # Anchor current vectors at their dates; opposite hourly flows can cancel out:
        ocean_axes[3].axhline(0, color="0.65", linewidth=1, zorder=1)
        ocean_axes[3].plot(ocean_comparison.index, np.zeros(len(ocean_comparison)), ".", color="0.4", zorder=2)
        # Start with a ±0.1 m/s side scale, expanding it if a future vector is stronger:
        current_vector_speed = np.hypot(ocean_comparison["current_east_ms"], ocean_comparison["current_north_ms"])
        current_vector_limit = max(0.1, 0.05 * np.ceil(current_vector_speed.fillna(0).max() / 0.05))
        ocean_axes[3].set_ylim(-current_vector_limit, current_vector_limit)
        current_arrows = ocean_axes[3].quiver(
            mdates.date2num(ocean_comparison.index), np.zeros(len(ocean_comparison)),
            ocean_comparison["current_east_ms"], ocean_comparison["current_north_ms"],
            angles="uv", scale_units="y", scale=1, units="dots", width=3,
            pivot="tail", color="teal", zorder=3,
        )
        ocean_axes[3].set_title("Mean current flow direction · north ↑, east →", loc="left")
        ocean_axes[3].set_ylabel("Velocity scale (m/s)")
        ocean_axes[3].set_yticks(np.linspace(-current_vector_limit, current_vector_limit, 5))
        # Leave room for sideways currents at the ends of the timeline:
        ocean_axes[3].margins(x=0.15)
        ocean_axes[4].plot(ocean_comparison.index, ocean_comparison["sea_level_msl_m"], marker="o", color="purple")
        ocean_axes[4].set_title("Daily mean sea level relative to mean sea level")
        ocean_axes[4].set_ylabel("Sea level (m)")
        ocean_axes[4].set_xlabel("Date (UTC)")
        for ocean_axis in ocean_axes:
            ocean_axis.grid(True, alpha=0.3)
        ocean_axes[4].xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
        ocean_axes[4].xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ocean_figure.tight_layout()
else:
    print("Run ingestion to save both hourly_marine.csv and hourly_salinity.csv for the ocean comparison.")

# Open the figures to explore the saved forecasts and their daily changes:
plt.show()
