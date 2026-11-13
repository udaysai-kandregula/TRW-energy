import json
import base64
import os
from pathlib import Path

out_dir = Path("frontend_assets")
out_dir.mkdir(exist_ok=True)
plots_dir = out_dir / "plots"
plots_dir.mkdir(exist_ok=True)

with open('Coding/Final_TRW (1).ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

extracted_plots = []
tables = {}

plot_names = {
    21: "03_voltage_full_overview.png",
    22: "04_voltage_day_trend.png",
    23: "05_voltage_week_trend.png",
    24: "06_voltage_month_raw_trend.png",
    25: "06b_voltage_month_daily_avg.png",
    27: "07_data_gaps_timeline.png",
    28: "08_time_intervals_distribution.png",
    31: "09_hourly_and_seasonal_trends.png",
    32: "10_sub_metering_zones.png",
    42: "09_model_test_zoomed_comparison.png",
    43: "10_confusion_matrices.png",
    44: "04_random_forest_feature_importance.png",
    45: "05_permutation_importance.png",
    47: "06_shap_summary_high_consumption.png",
    55: "07_pandas_vs_pyspark_explanatory.png",
    58: "saved_display_plots.png",
    59: "11_random_forest_roc_curve.png"
}

img_counter = 1
for i, cell in enumerate(nb['cells']):
    for out in cell.get('outputs', []):
        data = out.get('data', {})
        if 'image/png' in data:
            name = plot_names.get(i, f"cell_{i}_plot_{img_counter}.png")
            # If multiple images in cell
            img_path = plots_dir / name
            if img_path.exists():
                name = f"cell_{i}_plot_{img_counter}_{name}"
                img_path = plots_dir / name
            with open(img_path, 'wb') as img_f:
                img_f.write(base64.b64decode(data['image/png']))
            extracted_plots.append((i, str(img_path)))
            img_counter += 1

print(f"Extracted {len(extracted_plots)} plots successfully:")
for cell_i, p in extracted_plots:
    print(f"  Cell {cell_i} -> {p}")

