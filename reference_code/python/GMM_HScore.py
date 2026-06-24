import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from scipy.stats import norm
import os

def run_intensity_report(file_path, id_col, val_col, mode='fluorescence'):
    # 1. Load Data
    sep = '\t' if file_path.endswith(('.tsv', '.txt')) else ','
    print(f"--- Loading File: {os.path.basename(file_path)} ---")
    df = pd.read_csv(file_path, sep=sep, low_memory=False)
    df.columns = df.columns.str.strip()
    
    # 2. Pre-processing
    df[val_col] = pd.to_numeric(df[val_col], errors='coerce')
    min_raw, max_raw = df[val_col].min(), df[val_col].max()
    
    if mode.lower() == 'brightfield':
        processed_data = np.log10(255 / df[val_col].clip(1, 254))
        math_label = "Optical Density (OD)"
    else:
        processed_data = np.log10(df[val_col].clip(1, None))
        math_label = "Log10 Intensity Threshold"
        
    df['processed_val'] = processed_data
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=['processed_val'])
    data = df['processed_val'].values.reshape(-1, 1)
    
    # 3. Frequency Weighting (equal vote per slide, robust to cellularity imbalance)
    slide_counts = df[id_col].value_counts()
    inv_weights = (1.0 / df[id_col].map(slide_counts)).values
    base = inv_weights / inv_weights.min()             # max-cellularity slide -> 1.0
    MAX_WEIGHTED_ROWS = 3_000_000                       # memory budget for expansion
    resolution = max(1, int(MAX_WEIGHTED_ROWS / base.sum()))
    repeat_factor = np.clip(np.rint(base * resolution).astype(int), 1, None)
    weighted_data = np.repeat(data, repeat_factor, axis=0)
    
    # 4. Fit GMM (3 Components: 1+, 2+, 3+)
    print("Fitting GMM for Positive Populations (1+, 2+, 3+)...")
    gmm = GaussianMixture(n_components=3, covariance_type='full', random_state=42)
    gmm.fit(weighted_data)
    idx = np.argsort(gmm.means_.flatten())
    means = gmm.means_[idx].flatten()
    vars = gmm.covariances_[idx].flatten()
    props = gmm.weights_[idx].flatten()
    
    # 5. Threshold Calculation
    thresh_math = []
    for i in range(2):
        search_range = np.linspace(means[i], means[i+1], 1000).reshape(-1, 1)
        probs = gmm.predict_proba(search_range)[:, idx]
        crossing = np.where(probs[:, i+1] > probs[:, i])[0]
        if len(crossing) > 0:
            thresh_math.append(float(search_range[crossing[0], 0]))
        else:
            thresh_math.append(means[i] + (means[i+1] - means[i]) / 2)

    # 6. Reverse Mapping & Range Definition
    if mode.lower() == 'brightfield':
        t1, t2 = 255 / (10**thresh_math[0]), 255 / (10**thresh_math[1])
        ranges = [f"{max_raw:.2f} - {t1:.2f}", f"{t1-0.01:.2f} - {t2:.2f}", f"{t2-0.01:.2f} - {min_raw:.2f}"]
    else:
        t1, t2 = 10**thresh_math[0], 10**thresh_math[1]
        ranges = [f"{min_raw:.2f} - {t1:.2f}", f"{t1+0.01:.2f} - {t2:.2f}", f"{t2+0.01:.2f} - {max_raw:.2f}"]

    # 7. Visualization
    fig, (ax, ax_tbl) = plt.subplots(1, 2, figsize=(16, 7), gridspec_kw={'width_ratios': [1.2, 0.8]})
    x_plot = np.linspace(data.min(), data.max(), 1000).reshape(-1, 1)
    ax.hist(data, bins=100, density=True, alpha=0.1, color='k', label='Positive Cell Distribution')
    
    colors, bin_labels = ['#ffe145', '#ff7f0e', '#d62728'], ['Weak (1+)', 'Mod (2+)', 'Strong (3+)']
    for i in range(3):
        y = props[i] * norm.pdf(x_plot, means[i], np.sqrt(vars[i]))
        ax.plot(x_plot, y, label=bin_labels[i], color=colors[i], lw=2.5)
        if i < 2: ax.axvline(thresh_math[i], color='red', ls='--', alpha=0.5)

    ax.set_title(f"Positive Cell Intensity Classification", fontsize=14, fontweight='bold')
    ax.set_xlabel(f"Calculated Staining Level [{math_label}]")
    ax.set_ylabel("Probability Density")
    ax.legend(loc='upper right')

    # Table Appendix
    ax_tbl.axis('off')
    tbl_rows = [["Bin", "Intensity Range", "Population Weight"]] + \
               [[bin_labels[i], ranges[i], f"{props[i]:.1%}"] for i in range(3)] + \
               [["", "", ""], ["Boundary", "Intensity Threshold", math_label],
                ["1+ / 2+", f"{t1:.2f}", f"{thresh_math[0]:.3f}"],
                ["2+ / 3+", f"{t2:.2f}", f"{thresh_math[1]:.3f}"]]
    
    tbl = ax_tbl.table(cellText=tbl_rows, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(10.5); tbl.scale(1.1, 3.2)
    for (r, c), cell in tbl.get_celld().items():
        if r == 0 or r == 4: cell.set_text_props(fontweight='bold')

    plt.tight_layout()
    save_path = os.path.expanduser("~/Downloads/Intensity_Classification_Report.png")
    plt.savefig(save_path, dpi=300)
    print(f"--- SUCCESS ---\nReport saved to: {save_path}")
    plt.show()
    return [t1, t2]

# --- USER INPUT ---
FILE = r'/path/to/your/data.tsv'
ID_COL = 'Name'
VAL_COL = 'Positive Cell Intensity Per Object'
MODE = 'brightfield' 

final_cutoffs = run_intensity_report(FILE, ID_COL, VAL_COL, MODE)
