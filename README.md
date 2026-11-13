# PowerSense AI — Big Data Energy Consumption Prediction

An intelligent end-to-end web application and machine learning decision support dashboard for predicting household energy consumption demand levels (Low, Medium, High) 1 minute ahead.

Based on the research project report in `Docs/Energy_Consumption_Prediction_Project_Report_Final.pdf` and machine learning pipelines in `Coding/Final_TRW (1).ipynb`.

---

## ⚡ Highlights & Key Findings

- **Dataset**: UCI Machine Learning Repository — *Individual Household Electric Power Consumption* (1,048,575 rows, 9 attributes, sampled at 1-minute intervals over 2 full years from Dec 2006 to Dec 2008).
- **Target Horizons & Classes**: Future active power ($t+1$) categorized into three empirical quantile regimes:
  - **Low Demand**: $\le 0.336\text{ kW}$ (Standby / Off-peak night loads)
  - **Medium Demand**: $0.336\text{ kW} - 1.402\text{ kW}$ (Normal daytime household routines)
  - **High Demand**: $> 1.402\text{ kW}$ (Peak loads: HVAC, Water Heater, Cooking)
- **Top Performing Model**: **Random Forest Classifier** achieving **95.18% Accuracy** and **95.27% Macro F1 Score** on 156,584 unseen test samples.
- **Explainable AI (XAI)**:
  - Gini Feature Importance & Permutation Importance prove `Global_active_power` (0.280 Gini / 0.525 Permutation drop), `power_lag_1` (0.223), and `Global_intensity` (0.202) dominate predictive decisions.
  - TreeExplainer SHAP plots reveal how high amperage and sustained lag values drive transitions into the High Demand state.
- **Big Data Showdown**:
  - In-memory **Pandas** completed full descriptive aggregations in **0.1500 seconds**, whereas local **PySpark** took **10.6124 seconds** due to JVM startup and Py4J IPC serialization overhead on this single-node dataset size.

---

## 🚀 How to Run the Frontend

### Option 1: Native Web Dashboard & REST API (Currently Running!)

Runs immediately with Python's built-in standard library (no extra pip packages required):

```bash
python server.py 8000
```

Open your browser at:  
👉 **[http://localhost:8000](http://localhost:8000)**

#### Available REST API Endpoints:
- `GET  /api/health` — Check server status, model metadata, and accuracy.
- `GET  /api/metrics` — Retrieve full validation and test metrics across all 5 evaluated classifiers.
- `GET  /api/scenarios` — Load scenario presets and 18 real-world UCI test rows with ground truth.
- `POST /api/predict` — Submit real-time telemetry inputs (active power, intensity, voltage, lags) and receive demand class prediction with class probabilities.

---

### Option 2: Streamlit Dashboard (Option A from Notebook)

If you have or install Streamlit:

```bash
pip install streamlit pandas numpy joblib scikit-learn
streamlit run app.py
```

Open your browser at:  
👉 **[http://localhost:8501](http://localhost:8501)**

---

### Option 3: FastAPI Backend (Option B from Notebook)

If you prefer FastAPI + Swagger interactive docs:

```bash
pip install fastapi uvicorn pydantic
python api.py
```

Swagger API Docs:  
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## 📁 Repository Structure

```
TRW-energy/
├── Docs/
│   └── Energy_Consumption_Prediction_Project_Report_Final.pdf
├── Coding/
│   ├── Final_TRW (1).ipynb
│   ├── dump_nb.py
│   ├── extract_assets.py
│   ├── train_ensemble.py
│   └── generate_samples.py
├── DataSet/
│   └── household_power_consumption.csv
├── frontend/
│   ├── index.html            # Main web UI dashboard
│   ├── style.css             # High-contrast dark glassmorphism styling
│   ├── app.js                # Real-time slider bindings, client inference & presets
│   ├── rf_model.json         # Serialized Random Forest decision tree ensemble
│   ├── sample_scenarios.json # Presets & 18 UCI dataset historical test cases
│   ├── extracted_data.json   # Model evaluation tables and metadata
│   └── plots/                # Extracted PNG charts from the notebook (ROC, SHAP, CM, EDA)
├── server.py                 # Pure Python HTTP server & REST API
├── app.py                    # Streamlit frontend application
├── api.py                    # FastAPI REST endpoint
└── README.md
```

