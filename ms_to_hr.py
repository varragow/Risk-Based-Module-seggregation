def convert_ms_to_hms(milliseconds):
    seconds = milliseconds // 1000
    milliseconds = milliseconds % 1000
    minutes = seconds // 60
    seconds = seconds % 60
    hours = minutes // 60
    minutes = minutes % 60

    return hours, minutes, seconds, milliseconds


# Example usage
milliseconds = 154884903
hours, minutes, seconds, milliseconds = convert_ms_to_hms(milliseconds)
print(
    f"{milliseconds} ms is equal to {hours} hours, {minutes} minutes, {seconds} seconds, and {milliseconds} milliseconds.")