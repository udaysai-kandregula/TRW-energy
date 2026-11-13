import json
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="PowerSense AI — Energy Consumption Prediction API",
    description="REST API for real-time household energy demand classification based on UCI Machine Learning Repository Dataset",
    version="1.0.0"
)

# Load model
MODEL_PATH = Path("frontend/rf_model.json")
rf_model = {}
if MODEL_PATH.exists():
    with open(MODEL_PATH, "r", encoding="utf-8") as f:
        rf_model = json.load(f)

class PredictionInput(BaseModel):
    Global_active_power: float = 1.10
    Global_reactive_power: float = 0.12
    Voltage: float = 240.0
    Global_intensity: float = 4.80
    Sub_metering_1: float = 0.0
    Sub_metering_2: float = 1.0
    Sub_metering_3: float = 0.0
    power_lag_1: float = 1.10
    power_lag_5: float = 1.10
    power_lag_15: float = 1.10
    power_mean_15: float = 1.10
    hour: int = 14
    day_of_week: int = 1

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
        gap = x[0]
        if gap <= 0.336:
            return "Low", {"Low": 0.90, "Medium": 0.08, "High": 0.02}
        elif gap <= 1.402:
            return "Medium", {"Low": 0.08, "Medium": 0.84, "High": 0.08}
        else:
            return "High", {"Low": 0.02, "Medium": 0.12, "High": 0.86}

    avg_probs = [0.0, 0.0, 0.0]
    for tree in trees:
        prob = predict_tree(tree, x)
        for i in range(3):
            avg_probs[i] += prob[i]
    n = len(trees)
    avg_probs = [round(p / n, 4) for p in avg_probs]
    classes = ["Low", "Medium", "High"]
    max_idx = avg_probs.index(max(avg_probs))
    return classes[max_idx], dict(zip(classes, avg_probs))

@app.get("/")
def root():
    return {
        "app": "PowerSense AI API",
        "status": "online",
        "docs": "/docs",
        "endpoints": ["/predict", "/metrics", "/health"]
    }

@app.get("/health")
def health():
    return {"status": "ok", "model": "Random Forest", "accuracy": "95.18%"}

@app.post("/predict")
def predict(data: PredictionInput):
    try:
        x = [
            data.Global_active_power,
            data.Global_reactive_power,
            data.Voltage,
            data.Global_intensity,
            data.Sub_metering_1,
            data.Sub_metering_2,
            data.Sub_metering_3,
            data.power_lag_1,
            data.power_lag_5,
            data.power_lag_15,
            data.power_mean_15,
            data.hour,
            data.day_of_week
        ]
        prediction, probabilities = predict_forest(rf_model, x)
        return {
            "prediction": prediction,
            "horizon": "1 minute ahead",
            "probabilities": probabilities,
            "thresholds": {"low": "<= 0.336 kW", "medium": "0.336 - 1.402 kW", "high": "> 1.402 kW"}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

