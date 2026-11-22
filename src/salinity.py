from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import copernicusmarine
import pandas as pd


# Download and save surface salinity for the same forecast dates as our ocean batch:
def collect_salinity(latitude, longitude, start_time, end_time):
    dataset_id = "cmems_mod_bal_phy_anfc_PT1H-i"

    # Open the nearest grid cell without assuming that the model has a zero-metre layer:
    with copernicusmarine.open_dataset(
        dataset_id=dataset_id,
        variables=["so"],
        minimum_latitude=latitude,
        maximum_latitude=latitude,
        minimum_longitude=longitude,
        maximum_longitude=longitude,
        start_datetime=start_time,
        end_datetime=end_time,
        coordinates_selection_method="nearest",
    ) as dataset:
        # Select the shallowest actual depth before downloading the salinity values:
        dataset = dataset.sel(depth=[dataset["depth"].min().item()])
        dataset.load()
        downloaded_at = datetime.now(timezone.utc)

        # Keep the original subset and its units, depth, and grid coordinates:
        raw_folder = Path("data/raw")
        raw_folder.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            dir=raw_folder,
            prefix=f"salinity_{downloaded_at.strftime('%Y%m%dT%H%M%S%fZ')}_",
            suffix=".nc", delete=False,
        ) as raw_file:
            raw_path = Path(raw_file.name)
        dataset.to_netcdf(raw_path, engine="h5netcdf")
        print(f"Saved original salinity subset to {raw_path}")

        # Keep the salinity values with their actual sample times and model location:
        salinity_df = dataset[["so"]].to_dataframe().reset_index()
        salinity_df = salinity_df.rename(columns={"so": "sss"})
        salinity_df = salinity_df[["time", "sss", "depth", "latitude", "longitude"]]
        salinity_df["time"] = pd.to_datetime(salinity_df["time"], utc=True)
        salinity_df["downloaded_at"] = downloaded_at.isoformat()
        salinity_df["dataset_id"] = dataset_id
        salinity_df["salinity_units"] = dataset["so"].attrs.get("units", "unknown")

    # Stop if the selected point has no ocean salinity, for example on a land cell:
    if salinity_df.empty or not salinity_df["sss"].notna().any():
        raise ValueError("No surface salinity is available at the selected Copernicus grid cell.")

    # Preserve each downloaded salinity forecast as a separate batch:
    history_path = Path("data/processed/hourly_salinity.csv")
    if history_path.exists():
        saved_salinity = pd.read_csv(history_path, dtype={"salinity_units": str})
        salinity_df = pd.concat([saved_salinity, salinity_df], ignore_index=True)
    salinity_df["time"] = pd.to_datetime(salinity_df["time"], utc=True)
    salinity_df = salinity_df.drop_duplicates(subset=["downloaded_at", "time"], keep="last")
    salinity_df = salinity_df.sort_values(["downloaded_at", "time"])
    history_path.parent.mkdir(parents=True, exist_ok=True)

    # Replace the saved CSV only after the complete new history has been written:
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=history_path.parent,
        prefix="salinity_", suffix=".csv", delete=False, newline="",
    ) as temporary_file:
        salinity_df.to_csv(temporary_file, index=False)
        temporary_path = Path(temporary_file.name)
    temporary_path.replace(history_path)
    print(f"Saved {len(salinity_df)} hourly salinity forecast records to {history_path}")
