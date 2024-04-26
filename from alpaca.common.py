from datetime import datetime, timedelta

def rd(dt):
    # Extract minutes, seconds, and microseconds
    minute = dt.minute
    seconds = dt.second
    microseconds = dt.microsecond
    
    # Find how many minutes to subtract to round down to the nearest 15-minute interval
    minute_to_subtract = minute % 15
    
    # Subtract the extra minutes, all seconds, and all microseconds
    rounded_dt = dt - timedelta(minutes=minute_to_subtract, seconds=seconds, microseconds=microseconds)
    
    return rounded_dt

# Test cases
times = [
    datetime(2023, 4, 24, 10, 15, 0, 1),
    datetime(2023, 4, 24, 10, 16, 0),
    datetime(2023, 4, 24, 10, 30, 0, 500000),
    datetime(2023, 4, 24, 10, 45, 59, 999999),
    datetime(2023, 4, 24, 11, 0, 0, 0)
]

# Applying the rounding function
for t in times:
    print(f"Original: {t}, Rounded: {rd(t)}")