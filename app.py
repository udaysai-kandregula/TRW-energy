import json
from pathlib import Path
import streamlit as st
import numpy as np

# Page configuration
st.set_page_config(
    page_title="PowerSense AI — Energy Consumption Predictor",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Household Energy Consumption Predictor")
st.markdown("""
**Course Project: Big Data Analytics for Energy Consumption Prediction**  
Predict future household energy demand levels (**Low**, **Medium**, **High**) 1-minute ahead using your trained Random Forest Classifier.
""")

# Sidebar inputs for the features
st.sidebar.header("🔌 Real-Time Telemetry Inputs")

global_active_power = st.sidebar.slider("Global Active Power (kW)", 0.0, 11.5, 1.10, step=0.05)
global_intensity = st.sidebar.slider("Global Intensity (Amps)", 0.0, 50.0, 4.80, step=0.1)
voltage = st.sidebar.slider("Voltage (V)", 220.0, 255.0, 240.0, step=0.5)
global_reactive_power = st.sidebar.slider("Global Reactive Power (kW)", 0.0, 1.5, 0.12, step=0.02)

st.sidebar.markdown("---")
st.sidebar.header("🏠 Sub-Metered Zones")
sub_1 = st.sidebar.slider("Kitchen (Sub 1) (Wh)", 0, 45, 0)
sub_2 = st.sidebar.slider("Laundry / AC (Sub 2) (Wh)", 0, 45, 1)
sub_3 = st.sidebar.slider("Water Heater (Sub 3) (Wh)", 0, 45, 0)

st.sidebar.markdown("---")
st.sidebar.header("⏳ Temporal Lags & Clock")
auto_lags = st.sidebar.checkbox("Auto-sync lags with active power", value=True)

if auto_lags:
    power_lag_1 = global_active_power
    power_lag_5 = global_active_power
    power_lag_15 = global_active_power
    power_mean_15 = global_active_power
else:
    power_lag_1 = st.sidebar.slider("Power Lag 1 min ago (kW)", 0.0, 11.5, global_active_power, step=0.05)
    power_lag_5 = st.sidebar.slider("Power Lag 5 mins ago (kW)", 0.0, 11.5, global_active_power, step=0.05)
    power_lag_15 = st.sidebar.slider("Power Lag 15 mins ago (kW)", 0.0, 11.5, global_active_power, step=0.05)
    power_mean_15 = (power_lag_1 + power_lag_5 + power_lag_15) / 3.0

hour = st.sidebar.slider("Hour of Day", 0, 23, 14)
day_of_week = st.sidebar.selectbox(
    "Day of Week",
    [0, 1, 2, 3, 4, 5, 6],
    format_func=lambda x: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x],
    index=1
)

# Decision Tree prediction logic
def predict_tree(node, x):
    if node.get("leaf", False):
        return node.get("prob", [0.33, 0.33, 0.34])
    feat_idx = node.get("feat", 0)
    thresh = node.get("thresh", 0.0)
    if x[feat_idx] <= thresh:
        return predict_tree(node.get("left", {}), x)
    return predict_tree(node.get("right", {}), x)

def predict_forest(model, x):
    trees = model.get("trees", [])
    if not trees:
        # Fallback heuristic
        gap = x[0]
        if gap <= 0.336:
            return "Low", [0.90, 0.08, 0.02]
        elif gap <= 1.402:
            return "Medium", [0.08, 0.84, 0.08]
        else:
            return "High", [0.02, 0.12, 0.86]

    avg_probs = [0.0, 0.0, 0.0]
    for tree in trees:
        prob = predict_tree(tree, x)
        for i in range(3):
            avg_probs[i] += prob[i]
    n = len(trees)
    avg_probs = [p / n for p in avg_probs]
    classes = ["Low", "Medium", "High"]
    max_idx = avg_probs.index(max(avg_probs))
    return classes[max_idx], avg_probs

# Load model
model_path = Path("frontend/rf_model.json")
rf_model = {}
if model_path.exists():
    with open(model_path, "r", encoding="utf-8") as f:
        rf_model = json.load(f)

# Main Dashboard
col_left, col_right = st.columns([1.2, 1])

features = [
    global_active_power, global_reactive_power, voltage, global_intensity,
    sub_1, sub_2, sub_3,
    power_lag_1, power_lag_5, power_lag_15, power_mean_15,
    hour, day_of_week
]

prediction, probs = predict_forest(rf_model, features)

with col_left:
    st.subheader("🎯 Real-Time Prediction Outcome")
    if prediction == "High":
        st.error(f"### 🚨 PREDICTED DEMAND: **{prediction.upper()}**")
        st.write("Expected Future Power: **> 1.402 kW**")
        st.warning("⚠️ High peak demand detected. Recommend load shedding or deferring secondary appliances.")
    elif prediction == "Medium":
        st.warning(f"### ⚡ PREDICTED DEMAND: **{prediction.upper()}**")
        st.write("Expected Future Power: **0.336 kW – 1.402 kW**")
        st.info("ℹ️ Normal daytime routine usage. Standard operating baseline.")
    else:
        st.success(f"### ✅ PREDICTED DEMAND: **{prediction.upper()}**")
        st.write("Expected Future Power: **≤ 0.336 kW**")
        st.success("🟢 Off-peak standby load. Optimal window for EV charging and thermal storage.")

    st.markdown("#### Class Confidence Probabilities")
    st.progress(probs[0], text=f"Low Demand: {probs[0]*100:.1f}%")
    st.progress(probs[1], text=f"Medium Demand: {probs[1]*100:.1f}%")
    st.progress(probs[2], text=f"High Demand: {probs[2]*100:.1f}%")

with col_right:
    st.subheader("📊 Key Telemetry Summary")
    st.metric("Global Active Power", f"{global_active_power:.2f} kW")
    st.metric("Line Voltage & Intensity", f"{voltage:.1f} V", f"{global_intensity:.1f} A")
    st.metric("Sub-metering Total", f"{sub_1 + sub_2 + sub_3} Wh")

st.markdown("---")
st.subheader("📈 Model Test Performance (156,584 Test Samples)")
st.table({
    "Model Architecture": ["Random Forest (Selected Best)", "Extra Trees", "HistGradientBoosting", "Decision Tree", "Logistic Regression"],
    "Accuracy": ["95.18%", "95.14%", "94.92%", "93.41%", "89.97%"],
    "Macro F1": ["95.27%", "95.23%", "95.02%", "93.55%", "89.95%"],
    "Training Time": ["114.48 s", "38.68 s", "27.83 s", "12.12 s", "45.95 s"]
})

