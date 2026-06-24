import pandas as pd
import matplotlib.pyplot as plt


# =========================
# CONFIGURATION (EDIT HERE)
# =========================
DEFAULT_CONFIG = {
    "sample_col": "Sample",
    "total_col": "Total_Positive_Cell_Percentage",

    "phenotype_cols": [
        "CD3+_Cell_Percentage",
        "CD4+_Cell_Percentage",
        "CD8+_Cell_Percentage",
        "CD3+CD4+_Cell_Percentage",
        "CD3+CD8+_Cell_Percentage",
        "CD3+CD4+CD8+_Cell_Percentage"
    ],

    "colors": {
        "CD3+_Cell_Percentage": "limegreen",
        "CD4+_Cell_Percentage": "yellow",
        "CD8+_Cell_Percentage": "red",
        "CD3+CD4+_Cell_Percentage": "pink",
        "CD3+CD8+_Cell_Percentage": "#C8A2C8",  # lilac
        "CD3+CD4+CD8+_Cell_Percentage": "maroon"
    },

    "title": "Stacked Positive Cell Percentages by Sample",
    "xlabel": "Sample",
    "ylabel": "Positive Cell Percentage (%)",
    "figsize": (12, 6),

    "validate_totals": True,
    "tolerance": 0.5  # allowed % difference
}


# =========================
# DATA LOADING
# =========================
def load_data(file_path):
    """
    Load CSV and normalize column names for easier handling.
    """
    df = pd.read_csv(file_path)

    # Normalize column names
    df.columns = df.columns.str.replace(r'[().^/ ]+', '_', regex=True)
    df.columns = df.columns.str.replace(r'__+', '_', regex=True)

    return df


# =========================
# VALIDATION
# =========================
def validate_data(df, config):
    """
    Ensure required columns exist and optionally validate totals.
    """
    required_cols = [config["sample_col"], config["total_col"]] + config["phenotype_cols"]

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if config["validate_totals"]:
        phenotype_sum = df[config["phenotype_cols"]].sum(axis=1)
        diff = (phenotype_sum - df[config["total_col"]]).abs()

        if (diff > config["tolerance"]).any():
            print("⚠️ Warning: Some rows do not sum to total within tolerance.")
            print(df.loc[diff > config["tolerance"], [config["sample_col"]]])


# =========================
# FONT SCALING
# =========================
def adjust_font_sizes(num_samples):
    if num_samples <= 6:
        return {"title": 18, "labels": 14, "ticks": 12}
    elif num_samples <= 12:
        return {"title": 16, "labels": 12, "ticks": 10}
    elif num_samples <= 25:
        return {"title": 14, "labels": 10, "ticks": 8}
    else:
        return {"title": 12, "labels": 9, "ticks": 7}


# =========================
# PLOTTING FUNCTION
# =========================
def create_stacked_barplot(df, config=DEFAULT_CONFIG):
    sample_col = config["sample_col"]
    total_col = config["total_col"]
    phenotype_cols = config["phenotype_cols"]
    colors = config["colors"]

    df[sample_col] = df[sample_col].astype(str)

    num_samples = df[sample_col].nunique()
    fonts = adjust_font_sizes(num_samples)

    plt.figure(figsize=config["figsize"])

    # Bottom tracker for stacking
    bottom = pd.Series([0] * len(df))

    # Plot each phenotype
    for phenotype in phenotype_cols:
        plt.bar(
            df[sample_col],
            df[phenotype],
            bottom=bottom,
            label=phenotype.replace("_Cell_Percentage", "").replace("_", " "),
            color=colors.get(phenotype, None),
            edgecolor="black"
        )
        bottom += df[phenotype]

    # Labels and styling
    plt.title(config["title"], fontsize=fonts["title"], weight="bold")
    plt.xlabel(config["xlabel"], fontsize=fonts["labels"])
    plt.ylabel(config["ylabel"], fontsize=fonts["labels"])

    plt.xticks(rotation=45, ha="right", fontsize=fonts["ticks"])
    plt.yticks(fontsize=fonts["ticks"])

    plt.legend(title="Phenotypes", bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.show()


# =========================
# MAIN PIPELINE
# =========================
def main(file_path, config=DEFAULT_CONFIG):
    df = load_data(file_path)
    validate_data(df, config)
    create_stacked_barplot(df, config)


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    file_path = "/path/to/your/data.csv"
    main(file_path)
