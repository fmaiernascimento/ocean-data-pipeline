
## My firts attemp was with NOAA data, but the dataset was never found... so we moved on. 
# url = (
#     "https://www.ncei.noaa.gov/erddap/search/index.json"
#     "?page=1&itemsPerPage=100&searchFor=sea%20surface%20temperature"
# )
# # to get what is the name of everything on the data:
# # {'table': {'columnNames' ....  'columnTypes' ...  'rows' ... } 

# # Get the dataset records returned by the search
# rows = data["table"]["rows"]

# # getting the column names to know which one is which
# column_names = data["table"]["columnNames"]

# # To verity which is the correct names of each column: 
# # ['griddap', 'Subset', 'tabledap', 'Make A Graph', 'wms', 'files', 'Title', 'Summary', 'Info', 'Background Info', 'RSS', 'Institution', 'Dataset ID']

# # getting the indexes of the things I want to see/exctract:
# title_ix = column_names.index("Title")
# dataset_id_ix = column_names.index("Dataset ID")
# institution_ix = column_names.index("Institution")

# # selecting a dataset:
# selected_dataset = None

# print(f"Number of datasets found: {len(rows)}")

# for row in rows:
#     #if row[dataset_id_ix] == "AEC_useast_satellite_climo":
#     #    selected_dataset = row
#     if "SST" in row[title_ix]:
#         print(f"Title: {row[title_ix]}")
#         print(f"Dataset ID: {row[dataset_id_ix]}")
#         print(f"Institution: {row[institution_ix]}")
#         print("-----------")

# # if selected_dataset is None:
# #     print("Dataset not found")
# # else: 
# #     print(f"Selected dataset: {selected_dataset[title_ix]}")
    


import requests # This is to get the dataset
import statistics # This is to get the statistics package
import validation # count_missing, count_invalid_data | since we used validation we need to do vailadion.count)missing | we could use from validation import count_missing, count_invalid_data


url = (
    "https://marine-api.open-meteo.com/v1/marine"
    "?latitude=54.1"
    "&longitude=12.1"
    "&hourly=sea_surface_temperature"
)

response = requests.get(url)
# response.raise_for_status()
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

    if temp < -2.5 or temp > 40:
        ii=ii+1

    i=i+1
    
print(f"Total timestamps: {i}")
print(f"Missing SST measurements: {im}")
print(f"Valid SST measurements: {jm}")
print(f"Invalid SST measurements: X: {ii}")
print("-----------")


# Doing first statistical analysis on the data:
minsst=min(sst)
maxsst=max(sst)
meansst=sum(sst)/len(sst)
sstdvsst=statistics.stdev(sst)   # Sample standard deviation (N-1)
pstdsst=statistics.pstdev(sst)  # Population standard deviation (N)

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

print("--------Test Data 1---")

test_data = [10.2, None, 10.5, 999.0, -300.0, 10.1]

print(f"Invalid SST: {validation.count_invalid_data(test_data, -2.5, 40)}")
print("-----------")

print("------Test Data 2-----")


test_data = [10.2, None, 999.0, -300.0, 10.5, None, 40.0, -2.5]

miss_data=validation.count_missing(test_data)
inval_data=validation.count_invalid_data(test_data,-2.5,40)

print(f"Total values: {len(test_data)} ")
print(f"Missing Values: {miss_data} ")
print(f"Invalid Values: {inval_data} ")
print(f"Valid values: {len(test_data)-(inval_data+miss_data)} ")
print("-----------")

