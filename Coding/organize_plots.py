import shutil
from pathlib import Path

plots = Path('frontend/plots')
mapping = {
    '10_confusion_matrices.png': 'cm_logistic_regression.png',
    'cell_43_plot_12_10_confusion_matrices.png': 'cm_decision_tree.png',
    'cell_43_plot_13_10_confusion_matrices.png': 'cm_random_forest.png',
    'cell_43_plot_14_10_confusion_matrices.png': 'cm_extra_trees.png',
    'cell_43_plot_15_10_confusion_matrices.png': 'cm_histgradientboosting.png',
    'cell_58_plot_21_saved_display_plots.png': '05_permutation_importance_display.png',
    'cell_58_plot_22_saved_display_plots.png': '07_pandas_vs_pyspark_display.png',
}

for src_name, dst_name in mapping.items():
    src = plots / src_name
    dst = plots / dst_name
    if src.exists():
        shutil.copy2(src, dst)
        print(f"Mapped {src_name} -> {dst_name}")

print("\nFiles in frontend/plots:")
for f in sorted(plots.glob('*.png')):
    print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")

