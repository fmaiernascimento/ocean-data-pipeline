
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
    


