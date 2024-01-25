import pandas as pd
import numpy as np

    #Note that you may need to install required libraries by running: pip install pandas numpy

def calculate_metrics(data):
    thickness = data["annotation area (um2)"] / data["skeleton length (um)"]

    q1 = np.percentile(thickness, 25)
    q2 = np.percentile(thickness, 50)
    q3 = np.percentile(thickness, 75)

    iqr = q3 - q1
    mean_thickness = np.mean(thickness)
    max_thickness = np.max(thickness)
    min_thickness = np.min(thickness)

    return q1, q2, q3, iqr, mean_thickness, max_thickness, min_thickness

def main():
    # Read the CSV file
    file_path = "/Users/revealbio/Downloads/23-739_Thickness/23-739_Thickness_CombinedData.csv"
    data = pd.read_csv(file_path)

    # Group data by "filename" and "region" and calculate thickness-related metrics for each group
    grouped_data = data.groupby(["filename", "region"]).apply(calculate_metrics)

    # Create a new DataFrame with the calculated metrics
    result_data = pd.DataFrame(grouped_data.tolist(), columns=[
        "Thickness 25th Percentile (Q1) (um)",
        "Thickness 50th Percentile (Q2/Median) (um)",
        "Thickness 75th Percentile (Q3) (um)",
        "Thickness Interquartile Range (Q3-Q1) (um)",
        "Mean Thickness (um)",
        "Max Thickness (um)",
        "Min Thickness (um)"
    ])

    result_data.insert(0, "Filename", grouped_data.index.get_level_values("filename"))
    result_data.insert(1, "Region", grouped_data.index.get_level_values("region"))

    # Specify the output directory and file name
    output_directory = "/Users/revealbio/Downloads/23-739_Thickness"
    output_file_name = "23-739_Thickness_Data.csv"
    output_file_path = f"{output_directory}/{output_file_name}"

    # Save the results to a new CSV file
    result_data.to_csv(output_file_path, index=False)
    print(f"Results saved to: {output_file_path}")

if __name__ == "__main__":
    main()
