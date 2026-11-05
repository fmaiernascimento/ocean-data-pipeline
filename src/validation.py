# Validation mathods:

#check for none data
def count_missing(data):
    result=0
    for value in data:
        if value is None:
            result += 1
    return result


#check for none and invalid (lowerd or higher then the limts) data:
def count_invalid_data(data, lower_limit, upper_limit):
    result = 0
    for value in data:
            if value is not None and (value < lower_limit or value > upper_limit):
                result += 1
    return result

