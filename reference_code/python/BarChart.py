import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def load_data(file_path):
    """
    Load the CSV file and normalize column names.
    Detect whether the data contains cell- or area-based percentages.
    """
    data = pd.read_csv(file_path)
    data.columns = data.columns.str.replace(r'[. ]+', '_', regex=True)

    # Detect the correct value column
    if 'Positive_Cell_Percentage' in data.columns:
        value_col = 'Positive_Cell_Percentage'
    elif 'Positive_Area_Percentage' in data.columns:
        value_col = 'Positive_Area_Percentage'
    else:
        raise ValueError("Expected 'Positive_Cell_Percentage' or 'Positive_Area_Percentage' in the data.")
    
    if 'Sample' not in data.columns:
        raise ValueError("The dataset must contain a 'Sample' column.")
    
    return data, value_col


def adjust_font_sizes(num_samples):
    """
    Adjust font sizes dynamically based on the number of samples.
    """
    if num_samples <= 6:
        return {"title": 18, "labels": 14, "ticks": 12}
    elif num_samples <= 12:
        return {"title": 16, "labels": 12, "ticks": 10}
    elif num_samples <= 25:
        return {"title": 14, "labels": 10, "ticks": 8}
    else:
        return {"title": 12, "labels": 9, "ticks": 7}


def create_barplot(data, value_col, bar_color="#59BBBB"):
    """
    Create a bar plot where each bar represents one data point (sample).
    """
    group_by = 'Sample'
    num_samples = data[group_by].nunique()
    font_sizes = adjust_font_sizes(num_samples)

    plt.figure(figsize=(max(8, num_samples * 0.5), 6))
    ax = sns.barplot(
        x=group_by,
        y=value_col,
        data=data,
        color=bar_color,
        edgecolor='black',
        errorbar=None
    )

    readable_label = value_col.replace("_", " ")
    ax.set_title(f'{readable_label} by Sample', fontsize=font_sizes["title"], weight='bold')
    ax.set_xlabel('Sample', fontsize=font_sizes["labels"])
    ax.set_ylabel(readable_label, fontsize=font_sizes["labels"])

    plt.xticks(rotation=45, ha='right', fontsize=font_sizes["ticks"])
    plt.yticks(fontsize=font_sizes["ticks"])

    plt.tight_layout()
    plt.show()


def main(file_path):
    data, value_col = load_data(file_path)

    # Ensure Sample is treated as string
    data['Sample'] = data['Sample'].astype(str)

    create_barplot(data, value_col=value_col)


if __name__ == '__main__':
    file_path = 'path/to/your/data.csv'
    main(file_path)
