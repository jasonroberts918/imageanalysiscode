import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Custom colors
custom_colors = ['#59BBBB']

# Function to plot box plot
def plot_boxplot(data, x_col, y_col):
    plt.figure(figsize=(8, 6))
    sns.boxplot(x=x_col, y=y_col, data=data, palette=custom_colors)
    plt.title(f'{y_col} by {x_col}', color='#000000')
    plt.xlabel(x_col, color='#000000')
    plt.ylabel(y_col, color='#000000')
    plt.xticks(rotation=45)
    plt.show()

# Function to plot violin plot
def plot_violinplot(data, x_col, y_col):
    plt.figure(figsize=(8, 6))
    sns.violinplot(x=x_col, y=y_col, data=data, palette=custom_colors)
    plt.title(f'{y_col} by {x_col}', color='#000000')
    plt.xlabel(x_col, color='#000000')
    plt.ylabel(y_col, color='#000000')
    plt.xticks(rotation=45)
    plt.show()

# Function to plot scatter plot
def plot_scatterplot(data, x_col, y_col):
    plt.figure(figsize=(8, 6))
    plt.scatter(data[x_col], data[y_col], color='#59BBBB')
    plt.title(f'{x_col} vs {y_col}', color='#000000')
    plt.xlabel(x_col, color='#000000')
    plt.ylabel(y_col, color='#000000')
    plt.show()

# Function to plot bar chart
def plot_barchart(data, x_col, y_col):
    plt.figure(figsize=(8, 6))
    sns.barplot(x=x_col, y=y_col, data=data, palette=custom_colors)  # Vertical bars
    plt.title(f'{y_col} by {x_col}', color='#000000')
    plt.xlabel(x_col, color='#000000')
    plt.ylabel(y_col, color='#000000')
    plt.xticks(rotation=45)
    plt.show()

# Function to generate grouped box plot
def plot_grouped_boxplot(data, x_col, y_col):
    plt.figure(figsize=(10, 6))
    sns.boxplot(x=x_col, y=y_col, data=data, palette=custom_colors)
    plt.title(f'{y_col} by {x_col}', color='#000000')
    plt.xlabel(x_col, color='#000000')
    plt.ylabel(y_col, color='#000000')
    plt.xticks(rotation=45)
    plt.show()

# Main function to load data and interact with user
def main():
    # Load data from CSV
    csv_file = 'patients_data.csv'
    data = pd.read_csv(csv_file)
    
    # Print columns to let user choose
    print("Columns in the CSV file:")
    print(data.columns)
    
    # Get user input for columns
    x_col = input("Enter the column name for X-axis: ").strip()
    y_col = input("Enter the column name for Y-axis: ").strip()
    
    # Plot based on user input
    plot_type = input("Enter plot type (box, violin, scatter, bar, grouped box): ").strip().lower()
    
    if plot_type == 'box':
        plot_boxplot(data, x_col, y_col)
    elif plot_type == 'violin':
        plot_violinplot(data, x_col, y_col)
    elif plot_type == 'scatter':
        plot_scatterplot(data, x_col, y_col)
    elif plot_type == 'bar':
        plot_barchart(data, x_col, y_col)
    elif plot_type == 'grouped box':
        plot_grouped_boxplot(data, x_col, y_col)
    else:
        print("Invalid plot type. Please choose from 'box', 'violin', 'scatter', 'bar', 'grouped box'.")

if __name__ == "__main__":
    main()
