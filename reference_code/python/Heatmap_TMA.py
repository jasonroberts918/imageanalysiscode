# Import necessary libraries
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Function to load and process the data
def load_data(file_path):
    """
    This function reads the CSV file and processes the column names to handle potential discrepancies.
    """
    # Load data from CSV file
    data = pd.read_csv(file_path)
    
    # Normalize column names by stripping any extra spaces or periods and replacing them with underscores
    data.columns = data.columns.str.replace(r'[. ]+', '_', regex=True)
    
    # Check if the necessary columns are present
    if 'Sample' not in data.columns or 'Positive_Cell_Percentage' not in data.columns:
        raise ValueError("The required columns 'Sample' and 'Positive_Cell_Percentage' are not found in the dataset.")
    
    return data

# Function to sort the Sample names in a way that handles both numeric and letter parts
def sort_samples(sample_column):
    """
    This function sorts the samples based on their numeric and alphabetical parts.
    It splits the sample name into two parts: a numeric and a string part.
    """
    # Use a lambda function to split and sort by both numeric and string parts of the sample
    sorted_samples = sorted(sample_column, key=lambda x: (int(''.join(filter(str.isdigit, x))), ''.join(filter(str.isalpha, x))))
    return sorted_samples

# Function to create the heatmap
def create_heatmap(data):
    """
    This function generates a 2D heatmap based on the given data.
    The heatmap represents the positive cell percentage for each sample.
    """
    # Sort data by Sample with custom sorting for names like '1A', '1B', etc.
    sorted_samples = sort_samples(data['Sample'])
    data_sorted = data.set_index('Sample').loc[sorted_samples].reset_index()

    # Extract values for positive cell percentage
    percentage_values = data_sorted['Positive_Cell_Percentage'].values

    # Organize samples by their letter part (row) and numeric part (column)
    col_dict = {}
    row_dict = {}
    
    # Organize samples into column (numeric part) and row (letter part) dicts
    for sample, percentage in zip(data_sorted['Sample'], percentage_values):
        row_letter = ''.join(filter(str.isalpha, sample))  # Extract letter part for rows
        col_number = ''.join(filter(str.isdigit, sample))  # Extract numeric part for columns
        
        if col_number not in col_dict:
            col_dict[col_number] = []
        col_dict[col_number].append(f'{sample}: {percentage:.2f}%')

        if row_letter not in row_dict:
            row_dict[row_letter] = []
        row_dict[row_letter].append(f'{sample}: {percentage:.2f}%')

    # Determine the number of rows and columns dynamically based on the data
    num_columns = len(col_dict)  # One column per unique number part
    num_rows = max(len(samples) for samples in col_dict.values())  # Max number of rows in any column

    # Initialize arrays for reshaped values
    reshaped_values = np.full((num_rows, num_columns), np.nan)  # Initialize with NaN for empty cells
    sample_names_reshaped = np.full((num_rows, num_columns), '', dtype=object)

    # Fill the reshaped arrays with data
    for col_index, (col_number, samples) in enumerate(sorted(col_dict.items())):
        for row_index, sample_info in enumerate(samples):
            sample_names_reshaped[row_index, col_index] = sample_info
            reshaped_values[row_index, col_index] = float(sample_info.split(":")[1].strip('%'))  # Extract percentage value

    # Set up the heatmap plot with seaborn
    plt.figure(figsize=(18, 14))  # Adjust the figsize as needed
    ax = sns.heatmap(reshaped_values, cmap='YlOrRd', annot=sample_names_reshaped, cbar=True,
                     annot_kws={'size': 9}, cbar_kws={'label': 'Positive Cell Percentage'}, 
                     xticklabels=False, yticklabels=False, fmt="")

    # Remove axis labels
    ax.set_xlabel('')
    ax.set_ylabel('')
    
    # Set the title
    ax.set_title('Heatmap of Positive Cell Percentage - LC2081a NEG')

    # Add a label to the color bar
    colorbar = ax.collections[0].colorbar
    colorbar.set_label('Positive Cell Percentage')

    # Show the heatmap
    plt.show()

# Main function to load data and create the heatmap
def main(file_path):
    """
    Main function to process the data and create the heatmap.
    """
    # Load data from the CSV file
    data = load_data(file_path)

    # Create the heatmap
    create_heatmap(data)

# Example usage
if __name__ == '__main__':
    # Replace with the path to your .csv file
    file_path = 'path/to/your/data.csv'
    main(file_path)
