#!/usr/bin/env python3
"""
PowerSense AI — Energy Consumption Prediction Server
Zero-dependency HTTP server & REST API serving the modern frontend
and model inference engine.
"""

import os
import sys
import json
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("PORT", 8000))
FRONTEND_DIR = Path(__file__).parent / "frontend"

# Load the Random Forest model and sample data
RF_MODEL_PATH = FRONTEND_DIR / "rf_model.json"
SCENARIOS_PATH = FRONTEND_DIR / "sample_scenarios.json"
METRICS_PATH = FRONTEND_DIR / "extracted_data.json"

rf_model = None
sample_scenarios = None
project_metrics = None

if RF_MODEL_PATH.exists():
    try:
        with open(RF_MODEL_PATH, "r", encoding="utf-8") as f:
            rf_model = json.load(f)
        print(f"Loaded Random Forest model with {len(rf_model.get('trees', []))} decision trees.")
    except Exception as e:
        print(f"Warning loading rf_model.json: {e}")

if SCENARIOS_PATH.exists():
    try:
        with open(SCENARIOS_PATH, "r", encoding="utf-8") as f:
            sample_scenarios = json.load(f)
        print(f"Loaded {len(sample_scenarios.get('historical_test_cases', []))} historical scenarios.")
    except Exception as e:
        print(f"Warning loading scenarios: {e}")

if METRICS_PATH.exists():
    try:
        with open(METRICS_PATH, "r", encoding="utf-8") as f:
            project_metrics = json.load(f)
    except Exception as e:
        print(f"Warning loading metrics: {e}")


def predict_tree(node, x):
    if node.get("leaf", False):
        return node.get("prob", [0.33, 0.33, 0.34])
    feat_idx = node.get("feat", 0)
    thresh = node.get("thresh", 0.0)
    if x[feat_idx] <= thresh:
        return predict_tree(node.get("left", {}), x)
    else:
        return predict_tree(node.get("right", {}), x)


def predict_forest(model, x):
    trees = model.get("trees", [])
    if not trees:
        # Fallback heuristic
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
    classes = model.get("classes", ["Low", "Medium", "High"])
    max_idx = avg_probs.index(max(avg_probs))
    pred_class = classes[max_idx]
    prob_dict = dict(zip(classes, avg_probs))
    return pred_class, prob_dict


class EnergyRequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS for local dev
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_HEAD(self):
        self.do_GET(head_only=True)

    def do_GET(self, head_only=False):
        parsed = urlparse(self.path)
        path = parsed.path

        # --- API ROUTES ---
        if path == "/api/health":
            self.send_json({
                "status": "online",
                "app": "PowerSense AI",
                "version": "1.0.0",
                "dataset_rows": 1048575,
                "best_model": "Random Forest",
                "accuracy": "95.18%"
            }, head_only=head_only)
            return

        if path == "/api/metrics":
            data = project_metrics or {}
            self.send_json(data, head_only=head_only)
            return

        if path == "/api/scenarios":
            data = sample_scenarios or {}
            self.send_json(data, head_only=head_only)
            return

        # --- STATIC FILE SERVING ---
        if path == "/" or path == "":
            path = "/index.html"

        file_path = FRONTEND_DIR / path.lstrip("/")

        # Prevent directory traversal
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(FRONTEND_DIR.resolve())):
                self.send_error(403, "Forbidden")
                return
        except Exception:
            self.send_error(400, "Bad Request")
            return

        if not file_path.exists() or file_path.is_dir():
            self.send_error(404, "File Not Found")
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            if not head_only:
                self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {e}")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/predict":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                payload = json.loads(body)

                # Feature order matching model:
                # [gap, grp, volt, gi, s1, s2, s3, lag1, lag5, lag15, mean15, hour, dow]
                features = [
                    float(payload.get("Global_active_power", 1.10)),
                    float(payload.get("Global_reactive_power", 0.12)),
                    float(payload.get("Voltage", 240.0)),
                    float(payload.get("Global_intensity", 4.80)),
                    float(payload.get("Sub_metering_1", 0.0)),
                    float(payload.get("Sub_metering_2", 1.0)),
                    float(payload.get("Sub_metering_3", 0.0)),
                    float(payload.get("power_lag_1", payload.get("Global_active_power", 1.10))),
                    float(payload.get("power_lag_5", payload.get("Global_active_power", 1.10))),
                    float(payload.get("power_lag_15", payload.get("Global_active_power", 1.10))),
                    float(payload.get("power_mean_15", payload.get("Global_active_power", 1.10))),
                    int(payload.get("hour", 12)),
                    int(payload.get("day_of_week", 1))
                ]

                pred_class, probs = predict_forest(rf_model or {}, features)
                
                self.send_json({
                    "success": True,
                    "prediction": pred_class,
                    "probabilities": probs,
                    "inputs_received": payload
                })
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=400)
            return

        self.send_error(404, "Endpoint not found")

    def send_json(self, data, status=200, head_only=False):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def log_message(self, format, *args):
        # Quieter logging for smooth dashboard operation
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")


def run(port=PORT):
    server_address = ("", port)
    httpd = HTTPServer(server_address, EnergyRequestHandler)
    print("=" * 65)
    print(f"⚡ PowerSense AI Server running at http://localhost:{port}")
    print(f"📁 Serving static assets from: {FRONTEND_DIR}")
    print(f"🔌 REST API Endpoints:")
    print(f"   GET  http://localhost:{port}/api/health")
    print(f"   GET  http://localhost:{port}/api/metrics")
    print(f"   GET  http://localhost:{port}/api/scenarios")
    print(f"   POST http://localhost:{port}/api/predict")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run(port_arg)
