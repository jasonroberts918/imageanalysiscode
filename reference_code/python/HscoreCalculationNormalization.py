import os
import pandas as pd

# Change path here, this is where your data is
path_det = "/Users/user/Downloads/detection results_intensity"
path_ano = "/Users/user/Downloads/annotation results_intensity"
os.chdir(path_det)

# Tells it to look for all .txt files in the path given above
filelist = [file for file in os.listdir(path_det) if file.endswith(".txt")]

# Makes the final summary table with 12 columns with those column headers in order, these can be changed if needed
DataDraft = pd.DataFrame(columns=[
    "Sample",
    "Cell Density (cells/mm^2)",
    "Cell Count",
    "Cell %",
    "Cell Intensity - Overall",
    "Min Intensity",
    "Med Intensity",
    "Max Intensity",
    "Lower 25th Percentile Intensity",
    "50th Percentile Intensity",
    "Upper 75th Percentile Intensity",
    "Cell Area (mm^2)",
    "NotCell Count",
    "NotCell Area (mm^2)",
    "Annotation Area (mm^2)",
    "Total Cell Count"
])



# For loop, for every file ending in .txt in that path, we will run through this loop of calculations once.
for f in filelist:
    # Declare some tables for data
    Read_Data = pd.DataFrame()
    Cell = pd.DataFrame()

    # This line reads the .txt file and places it into a table we can look at
    Read_Data = pd.read_csv(f, sep="\t", header=0)

    os.chdir(path_ano)
    filename = f.replace(" Detections", "")
    Read_Data_ano = pd.read_csv(filename, sep="\t", header=0)
    os.chdir(path_det)

    # Basic calculations from the data, NotCells are all the things that are given the class NotCell in the data etc, can be changed to be whatever
    NotCell = Read_Data[Read_Data["Class"] == "NotCell"]
    Cell = Read_Data[Read_Data["Class"] == "Cell"]

    NotCellArea = NotCell["Cell: Area µm^2"].sum() / 1000000  # division for conversion from um^2 to mm^2
    CellArea = Cell["Cell: Area µm^2"].sum() / 1000000  # division for conversion from um^2 to mm^2

    # if IF, use Cell["Cell..Green.mean"]
    # if HDAB, use Cell["Cell..DAB.OD.mean"]
    Mean_Intensity = Cell["DAB: Nucleus: Mean"].mean()

    # Normalize intensity data to fit the range of 0 to 1
    intensity_data = Cell["DAB: Nucleus: Mean"]
    normalized_intensity = (intensity_data - intensity_data.min()) / (intensity_data.max() - intensity_data.min())

    Quant_Intensity = normalized_intensity.quantile([0.25, 0.5, 0.75])

    Min_Intensity = normalized_intensity.min()
    Med_Intensity = normalized_intensity.median()
    Max_Intensity = normalized_intensity.max()

    Tot_Cells = len(Cell) + len(NotCell)
    realAnnotations = Read_Data_ano[Read_Data_ano["Name"] == "PathAnnotationObject"]
    anoArea = realAnnotations["Area µm^2"].sum() / 1000000  # division for conversion from um^2 to mm^2

    # DataDraft is the table where all of the calculations go from before, the brackets indicate the coordinate of where that calculation goes
    DataDraft.loc[k] = [
        filename.replace(".mrxs.txt", ""),
        len(Cell) / anoArea,
        len(Cell),
        len(Cell) / (len(Cell) + len(NotCell)),
        Mean_Intensity,
        Min_Intensity,
        Med_Intensity,
        Max_Intensity,
        Quant_Intensity[0.25],  # lower 25th percentile
        Quant_Intensity[0.5],  # 50th percentile
        Quant_Intensity[0.75],  # upper 75th percentile
        CellArea,
        len(NotCell),
        NotCellArea,
        anoArea,
        len(Cell) + len(NotCell)
    ]

    print(f)

    # The counter from before, k = k + 1, so essentially looking above we move to the next row in the table after one loop
    k = k + 1

# Writes a csv file with the data in the path
DataDraft.to_csv(f"Data_minmedmax_{f}_normalized.csv", index=False)
