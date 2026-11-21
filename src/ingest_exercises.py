# Practice the earlier counting, statistics, and Pandas exercises with a fresh batch:
import requests # This is to get the dataset
import statistics # This is to get the statistics package
import validation # count_missing, count_invalid_data | since we used validation we need to do vailadion.count)missing | we could use from validation import count_missing, count_invalid_data
import pandas as pd # we are going to play with tables :)
from pathlib import Path


url = (
    "https://marine-api.open-meteo.com/v1/marine"
    "?latitude=54.1"
    "&longitude=12.1"
    "&hourly=sea_surface_temperature"
)

# Stop if the server takes too long or returns an error:
response = requests.get(url, timeout=30)
response.raise_for_status()
print(response.status_code)

# get the data:
data = response.json()

# to get what is the data:
print(type(data))
print(data.keys())
print("-----------")


# to see what are the constest of hourly_units
print(data['hourly_units'])
print("-----------")

# to see what keys are in hourly
print(data["hourly"].keys())
print("-----------")

# Extracting trhe variables:
time = data["hourly"]["time"]
sst = data["hourly"]["sea_surface_temperature"]

# to see th etype and lenght of both times series:
print(type(time))
print(type(sst))
print("-----------")
print(len(time))
print(len(sst))
print("-----------")

# Organazing the data, seeing how many nones are, time steps and so on:
i = 0
im = 0
jm = 0
ii=0

for temp in sst:

    if temp is None:
        im = im+1
    else:
        jm = jm +1

        # Check the temperature limits only when a value is available:
        if temp < -2.5 or temp > 40:
            ii=ii+1

    i=i+1
    
print(f"Total timestamps: {i}")
print(f"Missing SST measurements: {im}")
print(f"Valid SST measurements: {jm}")
print(f"Invalid SST measurements: X: {ii}")
print("-----------")


# Leave missing values out of the calculations, keeping the original list for the timestamps:
available_sst = [temp for temp in sst if temp is not None]

# Stop before saving if the batch has no temperature values:
if not available_sst:
    raise ValueError("No SST values are available in this batch. The saved history has not been changed.")

# Doing first statistical analysis using the available values:
minsst=min(available_sst)
maxsst=max(available_sst)
meansst=sum(available_sst)/len(available_sst)
pstdsst=statistics.pstdev(available_sst)  # Population standard deviation (N)

# Sample standard deviation needs at least two values:
if len(available_sst) >= 2:
    sstdvsst=statistics.stdev(available_sst)   # Sample standard deviation (N-1)
else:
    sstdvsst=float("nan")

print(f"Minimum SST: {minsst:.2f} °C")
print(f"Maximum SST: {maxsst:.2f} °C")
print(f"Mean SST: {meansst:.2f} °C")
print(f"Mean SST: {meansst:.2f} °C")
print(f"Mean SST: {meansst:.2f} °C")
print(f"SST Sample standard deviation: {sstdvsst:.2f} °C")
print(f"SST Population standard deviation: {pstdsst:.2f} °C")
print("-----------")


# calling the functions:


print(f"Missing Values: {validation.count_missing(sst)} ")
print(f"Invalid Values: {validation.count_invalid_data(sst,-2.5,40)} ")
print("-----------")

# Playing with Pandas:

sst_df = pd.DataFrame({
    "time":time,
    "sst": sst
    })


sst_df["time"] = pd.to_datetime(sst_df["time"])

print("------PANDAS-----")

sst_df.info()

print(sst_df.shape)
print(sst_df.head(5))
print(sst_df.tail(5))
print(sst_df.head(-5))
print("-----------")



# understand what a DataFrame is and statistics with Pandas:
sst_df["sst"]
print(f"Minimum SST: {sst_df["sst"].min()}")
print(f"Maximum SST: {sst_df["sst"].max()}")
print("-----------")

# Extracting Nan Numbers 
val_data = 0
m_data = 0
miss_data = sst_df["sst"].isna()
for value in miss_data:
    if not value:
        val_data += 1
    else:
        m_data += 1
        

print(f"Missing Values: {m_data} ")
print(f"Valid values: {val_data} ")
print(f"Mean SST: {sst_df["sst"].mean()}") # Already do  a NanMean
print(f"Standard deviation SST: {sst_df["sst"].std(ddof=0)}")
print("-----------")


# Filtering 
warm_sst = sst_df[sst_df["sst"]>10]

warm_sst.info()
print(f"Maximum SST: {warm_sst["sst"].max()}")
print("-----------")



# Selecting just one day:

print(sst_df.iloc[::24])
print("-----------")

day10_sst = sst_df[(sst_df["time"] >= "2026-11-17 00:00:00") & (sst_df["time"] < "2026-11-18 00:00:00")]
day10_sst.info()

print(f"How many hourly measurements are available for that day? {day10_sst.shape[0]} hourly measurements")
print(f"What is the minimum SST? {day10_sst["sst"].min()} °C")
print(f"What is the maximum SST? {day10_sst["sst"].max()} °C")
print(f"What is the mean SST? {day10_sst["sst"].mean()} °C")
print("-----------")
print("-----------")


# using groupby():
sst_dt = sst_df["time"].dt.date
print((sst_dt))
print("-----------")

sst_df["sst"].groupby(sst_dt)
daily_mean = sst_df["sst"].groupby(sst_dt).mean()
# Leave days with no temperatures out of the new batch to preserve their saved values:
daily_mean = daily_mean.dropna()
print(daily_mean)
print("---daily mean--------")


daily_change = daily_mean.diff()
print(daily_change)
print("----daily change-------")

print(-(daily_change.min()))
# Finding the biggest drop needs at least one available daily change:
if daily_change.notna().any():
    print(daily_change.idxmin())
else:
    print("Not enough daily values to find the biggest drop.")
print("----Min and Max-------")

valid_change = daily_change.dropna()
print(valid_change)
print("----valid change-------")


# Keep the recovery example here in case we need it again:
# recovered_history = pd.Series(
#     [8.612500, 8.595833, 8.408333, 8.395833],
#     index=pd.to_datetime(
#         ["2026-11-15", "2026-11-16", "2026-11-17", "2026-11-18"]
#     ).date,
#     name="sst",
# )


# Earlier saving and comparison examples:
# # Saving the data:
# daily_mean.to_csv("data/processed/daily_sst.csv")


# print(saved_dmean.shape)
# print(saved_dmean)
# print("-----daily mean------")
# print(saved_dmean.shape)


# print(saved_dmean["sst"] - daily_mean)
