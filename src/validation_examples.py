# Try our validation functions with missing and out-of-range temperatures:
import validation

print("--------Test Data 1---")

test_data = [10.2, None, 10.5, 999.0, -300.0, 10.1]

print(f"Invalid SST: {validation.count_invalid_data(test_data, -2.5, 40)}")
print("-----------")

print("------Test Data 2-----")


test_data = [10.2, None, 999.0, -300.0, 10.5, None, 40.0, -2.5]

miss_data = validation.count_missing(test_data)
inval_data = validation.count_invalid_data(test_data,-2.5,40)

print(f"Total values: {len(test_data)} ")
print(f"Missing Values: {miss_data} ")
print(f"Invalid Values: {inval_data} ")
print(f"Valid values: {len(test_data)-(inval_data+miss_data)} ")
print("-----------")

