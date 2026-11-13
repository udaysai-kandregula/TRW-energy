import csv
import math
import random
import time

print("Testing pure Python dataset loader and decision tree trainer...")
start_time = time.time()

# Let's read 20,000 rows from DataSet/household_power_consumption.csv
data = []
count = 0
with open('DataSet/household_power_consumption.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    print("Header:", header)
    
    for row in reader:
        if not row or len(row) < 9:
            continue
        # Date,Time,Global_active_power,Global_reactive_power,Voltage,Global_intensity,Sub_metering_1,Sub_metering_2,Sub_metering_3
        try:
            gap = float(row[2])
            grp = float(row[3])
            volt = float(row[4])
            gi = float(row[5])
            s1 = float(row[6])
            s2 = float(row[7])
            s3 = float(row[8])
            data.append((row[0], row[1], gap, grp, volt, gi, s1, s2, s3))
            count += 1
            if count >= 30000:
                break
        except (ValueError, IndexError):
            continue

print(f"Loaded {len(data)} rows in {time.time() - start_time:.2f}s")

