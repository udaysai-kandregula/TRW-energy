import csv
import json
import math
import random
import time
from datetime import datetime

print("Building feature engineering and training ensemble...")
start_time = time.time()

rows = []
with open('DataSet/household_power_consumption.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    count = 0
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
            # parse date time
            # 16-12-2006, 17:24:00
            time_parts = r[1].split(':')
            hour = int(time_parts[0])
            date_parts = r[0].split('-')
            # day, month, year
            day = int(date_parts[0])
            month = int(date_parts[1])
            year = int(date_parts[2])
            # approximate day of week
            dow = datetime(year, month, day).weekday()
            rows.append({
                'gap': gap, 'grp': grp, 'volt': volt, 'gi': gi,
                's1': s1, 's2': s2, 's3': s3,
                'hour': hour, 'dow': dow
            })
            count += 1
            if count >= 60000:
                break
        except Exception:
            continue

print(f"Read {len(rows)} samples in {time.time() - start_time:.2f}s")

# Construct lagged features and target
dataset = []
# features: [gap, grp, volt, gi, s1, s2, s3, lag1, lag5, lag15, mean15, hour, dow]
for i in range(15, len(rows) - 1):
    curr = rows[i]
    fut = rows[i+1]['gap']
    lag1 = rows[i-1]['gap']
    lag5 = rows[i-5]['gap']
    lag15 = rows[i-15]['gap']
    mean15 = sum(rows[j]['gap'] for j in range(i-15, i)) / 15.0
    
    # Class: Low, Medium, High
    # Low <= 0.336 kW, Medium 0.336 - 1.402 kW, High > 1.402 kW
    if fut <= 0.336:
        label = 0 # Low
    elif fut <= 1.402:
        label = 1 # Medium
    else:
        label = 2 # High
        
    feat = [
        curr['gap'], curr['grp'], curr['volt'], curr['gi'],
        curr['s1'], curr['s2'], curr['s3'],
        lag1, lag5, lag15, mean15,
        curr['hour'], curr['dow']
    ]
    dataset.append((feat, label))

print(f"Engineered {len(dataset)} valid sequences.")

# Split into train and test
split_idx = int(len(dataset) * 0.8)
train_data = dataset[:split_idx]
test_data = dataset[split_idx:]

print(f"Train size: {len(train_data)}, Test size: {len(test_data)}")

# Simple, high-speed Decision Tree implementation
class Node:
    def __init__(self, is_leaf=False, pred=None, prob=None, feat_idx=None, threshold=None, left=None, right=None):
        self.is_leaf = is_leaf
        self.pred = pred
        self.prob = prob
        self.feat_idx = feat_idx
        self.threshold = threshold
        self.left = left
        self.right = right

    def to_dict(self):
        if self.is_leaf:
            return {'leaf': True, 'pred': self.pred, 'prob': self.prob}
        return {
            'leaf': False,
            'feat': self.feat_idx,
            'thresh': round(self.threshold, 4),
            'left': self.left.to_dict(),
            'right': self.right.to_dict()
        }

def gini_impurity(counts, total):
    if total == 0: return 0
    return 1.0 - sum((c / total) ** 2 for c in counts)

def best_split(data, feature_subset):
    best_gain = 0
    best_feat = None
    best_thresh = None
    best_left = None
    best_right = None
    
    n = len(data)
    total_counts = [0, 0, 0]
    for _, y in data:
        total_counts[y] += 1
    base_gini = gini_impurity(total_counts, n)
    
    for f in feature_subset:
        # Sample candidate thresholds
        values = sorted(set(x[f] for x, _ in data))
        if len(values) <= 1:
            continue
        # Take at most 10 quantiles
        step = max(1, len(values) // 10)
        candidates = values[::step]
        
        for thresh in candidates:
            left_counts = [0, 0, 0]
            right_counts = list(total_counts)
            left = []
            right = []
            for item in data:
                x, y = item
                if x[f] <= thresh:
                    left.append(item)
                    left_counts[y] += 1
                    right_counts[y] -= 1
                else:
                    right.append(item)
                    
            if not left or not right:
                continue
                
            n_l, n_r = len(left), len(right)
            gain = base_gini - (n_l/n * gini_impurity(left_counts, n_l) + n_r/n * gini_impurity(right_counts, n_r))
            if gain > best_gain:
                best_gain = gain
                best_feat = f
                best_thresh = thresh
                best_left = left
                best_right = right
                
    return best_gain, best_feat, best_thresh, best_left, best_right

def build_tree(data, depth=0, max_depth=8, min_samples=20, n_features=7):
    counts = [0, 0, 0]
    for _, y in data:
        counts[y] += 1
    total = len(data)
    prob = [round(c / total, 4) for c in counts]
    pred = counts.index(max(counts))
    
    if depth >= max_depth or total < min_samples or max(counts) == total:
        return Node(is_leaf=True, pred=pred, prob=prob)
        
    feat_subset = random.sample(range(13), min(n_features, 13))
    gain, f, thresh, left, right = best_split(data, feat_subset)
    
    if gain <= 0.0005 or not left or not right:
        return Node(is_leaf=True, pred=pred, prob=prob)
        
    left_node = build_tree(left, depth + 1, max_depth, min_samples, n_features)
    right_node = build_tree(right, depth + 1, max_depth, min_samples, n_features)
    return Node(is_leaf=False, feat_idx=f, threshold=thresh, left=left_node, right=right_node)

print("Training Random Forest ensemble (5 trees)...")
forest = []
for t in range(5):
    # Bootstrap sample
    bootstrap = [random.choice(train_data) for _ in range(min(15000, len(train_data)))]
    tree = build_tree(bootstrap, depth=0, max_depth=7, min_samples=25, n_features=6)
    forest.append(tree)
    print(f"  Tree {t+1} trained.")

def predict_tree(node, x):
    if node.is_leaf:
        return node.prob
    if x[node.feat_idx] <= node.threshold:
        return predict_tree(node.left, x)
    return predict_tree(node.right, x)

def predict_forest(forest, x):
    avg_probs = [0.0, 0.0, 0.0]
    for tree in forest:
        p = predict_tree(tree, x)
        for i in range(3):
            avg_probs[i] += p[i]
    avg_probs = [round(p / len(forest), 4) for p in avg_probs]
    pred = avg_probs.index(max(avg_probs))
    return pred, avg_probs

# Evaluate on test set
correct = 0
for x, y in test_data:
    p_pred, _ = predict_forest(forest, x)
    if p_pred == y:
        correct += 1

acc = correct / len(test_data)
print(f"Test Accuracy on {len(test_data)} samples: {acc * 100:.2f}%")

# Save model to JSON
model_json = {
    'features': [
        "Global_active_power", "Global_reactive_power", "Voltage", "Global_intensity",
        "Sub_metering_1", "Sub_metering_2", "Sub_metering_3",
        "power_lag_1", "power_lag_5", "power_lag_15", "power_mean_15",
        "hour", "day_of_week"
    ],
    'classes': ["Low", "Medium", "High"],
    'thresholds': {'low': 0.336, 'high': 1.402},
    'trees': [tree.to_dict() for tree in forest]
}

with open('frontend_assets/rf_model.json', 'w', encoding='utf-8') as f:
    json.dump(model_json, f, indent=2)

print("Saved trained model to frontend_assets/rf_model.json successfully!")

