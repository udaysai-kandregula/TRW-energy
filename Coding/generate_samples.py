import csv
import json
from datetime import datetime

samples = []
with open('DataSet/household_power_consumption.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    buffer = []
    for r in reader:
        if not r or len(r) < 9:
            continue
        try:
            gap = float(r[2])
            grp = float(r[3])
            volt = float(r[4])
            gi = float(r[5])
            s1 = float(r[6])
            s2 = float(r[7])
            s3 = float(r[8])
            tp = r[1].split(':')
            hour = int(tp[0])
            dp = r[0].split('-')
            dow = datetime(int(dp[2]), int(dp[1]), int(dp[0])).weekday()
            buffer.append({
                'date': r[0], 'time': r[1],
                'gap': gap, 'grp': grp, 'volt': volt, 'gi': gi,
                's1': s1, 's2': s2, 's3': s3,
                'hour': hour, 'dow': dow
            })
            if len(buffer) >= 20000:
                break
        except Exception:
            continue

# Sample 5 low, 5 medium, 5 high test cases
test_cases = []
targets_found = {'Low': 0, 'Medium': 0, 'High': 0}

for i in range(15, len(buffer) - 1):
    curr = buffer[i]
    fut = buffer[i+1]['gap']
    if fut <= 0.336:
        label = "Low"
    elif fut <= 1.402:
        label = "Medium"
    else:
        label = "High"
        
    if targets_found[label] < 6:
        targets_found[label] += 1
        lag1 = buffer[i-1]['gap']
        lag5 = buffer[i-5]['gap']
        lag15 = buffer[i-15]['gap']
        mean15 = round(sum(buffer[j]['gap'] for j in range(i-15, i)) / 15.0, 3)
        
        test_cases.append({
            'name': f"{label} Demand Sample ({curr['date']} {curr['time']})",
            'actual_demand': label,
            'actual_future_power_kw': round(fut, 3),
            'inputs': {
                'Global_active_power': curr['gap'],
                'Global_reactive_power': curr['grp'],
                'Voltage': curr['volt'],
                'Global_intensity': curr['gi'],
                'Sub_metering_1': curr['s1'],
                'Sub_metering_2': curr['s2'],
                'Sub_metering_3': curr['s3'],
                'power_lag_1': lag1,
                'power_lag_5': lag5,
                'power_lag_15': lag15,
                'power_mean_15': mean15,
                'hour': curr['hour'],
                'day_of_week': curr['dow']
            }
        })
    if all(v >= 6 for v in targets_found.values()):
        break

presets = [
    {
        'id': 'night_standby',
        'title': '🌙 Late Night Standby',
        'desc': 'Minimal power usage during midnight hours with only idle electronics.',
        'expected': 'Low',
        'inputs': {
            'Global_active_power': 0.238,
            'Global_reactive_power': 0.082,
            'Voltage': 244.5,
            'Global_intensity': 1.1,
            'Sub_metering_1': 0.0,
            'Sub_metering_2': 0.0,
            'Sub_metering_3': 0.0,
            'power_lag_1': 0.240,
            'power_lag_5': 0.236,
            'power_lag_15': 0.242,
            'power_mean_15': 0.239,
            'hour': 3,
            'day_of_week': 2
        }
    },
    {
        'id': 'daytime_moderate',
        'title': '☀️ Daytime Routine Usage',
        'desc': 'Standard daytime activity (fridge, computers, intermittent lighting).',
        'expected': 'Medium',
        'inputs': {
            'Global_active_power': 0.884,
            'Global_reactive_power': 0.126,
            'Voltage': 240.2,
            'Global_intensity': 3.8,
            'Sub_metering_1': 0.0,
            'Sub_metering_2': 1.0,
            'Sub_metering_3': 1.0,
            'power_lag_1': 0.890,
            'power_lag_5': 0.865,
            'power_lag_15': 0.872,
            'power_mean_15': 0.880,
            'hour': 14,
            'day_of_week': 1
        }
    },
    {
        'id': 'morning_cooking',
        'title': '🍳 Morning Cooking & Kitchen Surge',
        'desc': 'Microwave, kettle, and kitchen appliances operating during breakfast.',
        'expected': 'High',
        'inputs': {
            'Global_active_power': 2.450,
            'Global_reactive_power': 0.180,
            'Voltage': 238.1,
            'Global_intensity': 10.4,
            'Sub_metering_1': 18.0,
            'Sub_metering_2': 1.0,
            'Sub_metering_3': 0.0,
            'power_lag_1': 2.380,
            'power_lag_5': 2.150,
            'power_lag_15': 1.820,
            'power_mean_15': 2.110,
            'hour': 8,
            'day_of_week': 5
        }
    },
    {
        'id': 'evening_peak_heavy',
        'title': '⚡ Evening Peak Demand (HVAC + Water Heater)',
        'desc': 'Simultaneous heating, washing machine, and water heater operation.',
        'expected': 'High',
        'inputs': {
            'Global_active_power': 4.620,
            'Global_reactive_power': 0.410,
            'Voltage': 233.5,
            'Global_intensity': 19.8,
            'Sub_metering_1': 0.0,
            'Sub_metering_2': 18.0,
            'Sub_metering_3': 17.0,
            'power_lag_1': 4.580,
            'power_lag_5': 4.410,
            'power_lag_15': 4.200,
            'power_mean_15': 4.390,
            'hour': 19,
            'day_of_week': 4
        }
    }
]

out = {
    'presets': presets,
    'historical_test_cases': test_cases
}

with open('frontend_assets/sample_scenarios.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)

print(f"Generated {len(presets)} presets and {len(test_cases)} historical test cases.")

