#%% imports
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import math
import os
import glob

from pathlib import Path

#%%
class HeatmapMaker(object):

    def __init__(self, root_dir):
        #seaborn set
        sns.set()
        self.root_dir = root_dir  # the root folder containing all the files with ext
        self.ext = ".xlsx"
        os.chdir(self.root_dir)
        self.raw_files = glob.glob('*.xlsx')
        print(self.raw_files)
        print(len(self.raw_files))

        # Set manual heatmap value. Likely need to be matched across antibody
        self.max_heatmap_value = manual_thresh
        self.min_heatmap_value = 0

    def roundup(self, x):
        if x < 1:
            x = int(math.ceil(x))
        if (x >= 1) & (x < 10):
            x = int(math.ceil(x / 10.0)) * 10
        if (x >= 10) & (x < 1800):
            x = int(math.ceil(x / 100.0)) * 100
        if x >= 1800:
            x = int(math.ceil(x / 1000.0)) * 1000

        return x

    def simple_heatmap(self, df, heatmap_path):
        sns.set()

        cols = df.columns
        row_name = cols[0]
        col_name = cols[1]
        values_name = cols[2]
        h_min = self.min_heatmap_value
        h_max = self.max_heatmap_value

        # df = df.pivot(index = "Row",columns = "Column")

        #Change the commented line below to flip x and y axes
        #df = df.pivot(index=row_name, columns=col_name, values=values_name)
        df = df.pivot(index=col_name, columns=row_name, values=values_name)

        # Draw a heatmap with the numeric values in each cell
        #fig, ax = plt.subplots(figsize=(9, 6))
        fig, ax = plt.subplots(figsize=(18, 12))

        head, tail = os.path.split(heatmap_path)
        title_ext, ext = os.path.splitext(tail)
        title = title_ext + ': ' + values_name
        ax.set_title(title, fontsize = 18)

        h_min = 0
        # hMax
#        g = sns.heatmap(df, annot=True, fmt="0.1f", linewidths=.5, ax=ax, vmin=h_min, vmax=h_max, cmap="jet")
        #g = plt.figure(figsize=(10, 16))
        g = sns.heatmap(df, annot=True, annot_kws={"size": 12}, fmt="0.1f", cmap="jet", linewidths=.5, ax=ax, vmin=h_min, vmax=h_max)
        # g = sns.heatmap(df, annot=True, fmt="0.1f", linewidths=.5, ax=ax,vmin=hin, vmax=hMax, cmap = "jet")
        g.set(ylabel='')
        g.set(xlabel='')

        #ylabels = [str(int(str(x))) for x in g.get_yticklabels()]
        #g.set_yticklabels(ylabels, rotation=0)
        g.set_yticklabels(g.get_yticklabels(), rotation=0)
        
        #INVERT Y-AXIS
        g.invert_yaxis()

        fig.savefig(heatmap_path)
        #plt.show()
        print("heatmap finished")

    def heatmap_test(self):
        sns.set()

        # Load the example flights dataset and conver to long-form
        flights_long = sns.load_dataset("flights")
        flights = flights_long.pivot("month", "year", "passengers")
        print(flights_long.head())
        print(flights)

        # Draw a heatmap with the numeric values in each cell
        fig, ax = plt.subplots(figsize=(9, 6))
        sns.heatmap(flights, annot=True, fmt="d", linewidths=.5, ax=ax)
        plt.show()
        #fig.savefig('output.png')

        print("heatmapTest finished")

    def prepare_tma_for_heatmap(self, df):
        df = df.pivot(index="Row", columns="Column", values="PositiveDensity")
        return df

    def read_raw_qu_file(self):
        for infile in self.raw_files:
            # print(infile)
            #read in raw qupath datafile
            df = pd.read_csv(infile,encoding = "iso-8859-1",delimiter = '\t')
        return

    def xlsx_to_heatmaps(self):
        # df = pd.read_excel('File.xlsx', sheetname='Sheet1')
        print("xlsx to heatmaps")
        final_max = 1
        for f in self.raw_files:
            print(f)
            #df = get_data(f)
            df = pd.read_excel(f)
            df = df.drop(df[(df['Letter'] == "H") & (df["Number"] == 13)].index)  #Remove orientation core (manual)
            #print(df.head())
            cols = df.columns
            values_name = cols[2]
            temp_max = df[values_name].max()
            if temp_max > final_max:
                final_max = temp_max
            final_max = self.roundup(final_max)
            #print(final_max)

        #self.max_heatmap_value = final_max
        self.min_heatmap_value = 0
        print(self.max_heatmap_value)
        #
        for f in self.raw_files:
            # print f
            df = pd.read_excel(f)
            df = df.drop(df[(df['Letter'] == "H") & (df["Number"] == 13)].index)  #Remove orientation core (manual)
            heatmap_file = f.replace(self.ext, ".png")
            self.simple_heatmap(df, heatmap_file)

        return df

#%%

###FORMAT FOR INPUT: 3 columns --> 1) Row, 2) Column, 3) Data(typically positive density, column name matters for this

#Load example data and convert to long form

root_dir = r"/home/stacy/Documents/21-773 Inhibrix/CD3"
manual_thresh = 13000

print(os.listdir(root_dir))
print(root_dir)
hm = HeatmapMaker(root_dir)
hm.xlsx_to_heatmaps()


#hm.heatmap_test()
