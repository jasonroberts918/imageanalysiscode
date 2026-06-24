import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def load_data(file_path):
    """
    Load the CSV file and normalize column names.
    """
    data = pd.read_csv(file_path)
    data.columns = data.columns.str.replace(r'[. ]+', '_', regex=True)

    if 'Sample' not in data.columns or 'Total_Positive_Myonuclei_Percentage' not in data.columns:
        raise ValueError("Required columns 'Sample' and 'Total_Positive_Myonuclei_Percentage' not found.")
    
    return data

def create_boxplot(data, group_by='Sample', custom_palette=None):
    """
    Generate a boxplot grouped by 'Sample' or any specified column (e.g., 'Group', 'Donor').
    """
    if group_by not in data.columns:
        raise ValueError(f"The specified group_by column '{group_by}' is not in the dataset.")

    if custom_palette is None:
        unique_groups = data[group_by].unique()
        custom_palette = sns.color_palette("Set3", len(unique_groups))

    palette = dict(zip(data[group_by].unique(), custom_palette))

    plt.figure(figsize=(12, 6))
    ax = sns.boxplot(
        x=group_by,
        y='Total_Positive_Myonuclei_Percentage',
        data=data,
        palette=palette,
        hue=group_by,
    )

    sns.stripplot(
        x=group_by,
        y='Total_Positive_Myonuclei_Percentage',
        data=data,
        color='black',
        size=3,
        jitter=True,
        alpha=0.6
    )

    ax.set_title(f'Total Positive Myonuclei Percentage by {group_by}')
    ax.set_xlabel(group_by)
    ax.set_ylabel('Total Positive Myonuclei Percentage')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def main(file_path, group_by='Sample'):
    data = load_data(file_path)

    # Convert grouping column to string to avoid palette mismatches
    data[group_by] = data[group_by].astype(str)

    custom_colors = sns.color_palette("Set1", len(data[group_by].unique()))
    create_boxplot(data, group_by=group_by, custom_palette=custom_colors)

if __name__ == '__main__':
    file_path = '/path/to/your/data.csv'
    
    # Choose to group by 'Sample' or another column like 'Group'
    group_by_column = 'Group'  # Change to e.g. 'Group' if needed
    
    main(file_path, group_by=group_by_column)
