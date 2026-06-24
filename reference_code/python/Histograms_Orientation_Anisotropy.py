import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless plotting
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

sns.set_theme(style='whitegrid')
bar_color = "#59BBBB"

def add_summary_stats_text(ax, data):
    """Add min, max, mean, median stats as text box in a plot."""
    min_val = np.min(data)
    max_val = np.max(data)
    mean_val = np.mean(data)
    median_val = np.median(data)

    stats_text = (
        f"Min: {min_val:.3f}\n"
        f"Max: {max_val:.3f}\n"
        f"Mean: {mean_val:.3f}\n"
        f"Median: {median_val:.3f}"
    )
    ax.text(
        0.95, 0.95, stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='gray')
    )

def format_log_axis(ax):
    """Format y-axis in scientific notation (10^n)."""
    ax.set_yscale('log')
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda y, _: f"$10^{{{int(np.log10(y))}}}$" if y > 0 else "")
    )

def generate_histograms(csv_path, log_scale=True):
    # Load CSV with automatic delimiter detection
    df = pd.read_csv(csv_path, sep=None, engine='python', header=None,
                     names=['Sample', 'Anisotropy', 'Orientation'])

    # Clean and convert to numeric
    df['Anisotropy'] = pd.to_numeric(df['Anisotropy'], errors='coerce')
    df['Orientation'] = pd.to_numeric(df['Orientation'], errors='coerce')
    df = df.dropna(subset=['Anisotropy', 'Orientation'])

    output_dir = os.path.dirname(os.path.abspath(csv_path))

    for sample_id, group in df.groupby('Sample'):
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # --- Anisotropy Histogram ---
        sns.histplot(
            data=group,
            x='Anisotropy',
            bins=256,
            color=bar_color,
            kde=False,
            ax=axes[0]
        )
        axes[0].set_title(f'Sample {sample_id} - Anisotropy')
        axes[0].set_xlabel('Fiber Anisotropy Per Object')
        axes[0].set_ylabel('Frequency')
        axes[0].set_xlim(0, 1)
        if log_scale:
            format_log_axis(axes[0])
        add_summary_stats_text(axes[0], group['Anisotropy'])

        # --- Orientation Histogram ---
        bin_edges = np.linspace(-2, 2, 257)  # 256 bins from -2 to 2
        sns.histplot(
            data=group,
            x='Orientation',
            bins=bin_edges,
            color=bar_color,
            kde=False,
            ax=axes[1]
        )
        axes[1].set_title(f'Sample {sample_id} - Orientation')
        axes[1].set_xlabel('Fiber Orientation Per Object')
        axes[1].set_ylabel('Frequency')
        axes[1].set_xlim(-2, 2)
        axes[1].axvline(0, color='gray', linestyle='--', linewidth=1)
        if log_scale:
            format_log_axis(axes[1])
        add_summary_stats_text(axes[1], group['Orientation'])

        # Save combined figure
        plt.tight_layout()
        output_path = os.path.join(output_dir, f"{sample_id}_Histogram_Combined.png")
        plt.savefig(output_path, dpi=300)
        plt.close()

    print(f"\n✅ All histograms saved to: {output_dir}")

if __name__ == "__main__":
    # 🔁 Replace with your actual file path
    csv_file_path = "path/to/your/objectdata.csv"
    
    # Toggle log scale here:
    generate_histograms(csv_file_path, log_scale=True)
