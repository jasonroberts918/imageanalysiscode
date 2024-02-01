# Visualize DAPI Channel Distribution to
# assess signal variance within and across samples
import os
from numpy.lib.shape_base import tile
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn import manifold

data_path = "/home/user/dev/QC/GFAP/QC detection results - by cell"
category_name = "Sample"
feature = 'ROI: 1.00 µm per pixel: Blue: Median'
plot_title = 'Distribution of Signal Intensity'
x_label = feature

drop_columns = ['Image', 'Name', 'Class', 'Parent', 'ROI', 'Centroid X µm',
       'Centroid Y µm', 'Sample']

label_map = {'Negative': 0, 
             'Positive': 1,
             'Other': 2}

if os.path.isdir(data_path):
    tile_df = []
    for f in os.listdir(data_path):
        sample = f.replace(".mrxs.txt", "")
        df = pd.read_csv(os.path.join(data_path, f), sep='\t')
        df["Sample"] = sample
        tile_df.append(df)
    # tile_df = pd.concat(tile_df)
tile_df = tile_df[0]
tile_df.replace({'Class': label_map}, inplace=True)
tile_df.dropna(inplace=True)

X = tile_df.drop(columns=drop_columns)
y = tile_df["Class"]

print(X.shape)
print(y.shape)

### t-SNE
# n_samples = 150
n_components = 3
(fig, subplots) = plt.subplots(1, figsize=(24, 16))
# perplexities = [5, 30, 50, 100]
perplexity = 30

blue = y == 0
red = y == 1
yellow = y == 2

ax = subplots
# ax.scatter(X[blue, 0], X[blue, 1], c="b")
# ax.scatter(X[red, 0], X[red, 1], c="r")
# ax.scatter(X[yellow, 0], X[yellow, 1], c="y")
# ax.xaxis.set_major_formatter(NullFormatter())
# ax.yaxis.set_major_formatter(NullFormatter())
plt.axis("tight")

# for i, perplexity in enumerate(perplexities):
# ax = subplots[i]

# t0 = time()
tsne = manifold.TSNE(
    n_components=n_components,
    init="random",
    random_state=0,
    perplexity=perplexity,
    learning_rate="auto",
    n_iter=300,
)
Y = tsne.fit_transform(X)
# t1 = time()
print("circles, perplexity=%d" % (perplexity))
ax.set_title("Perplexity=%d" % perplexity)
# ax.scatter(Y[blue, 0], Y[blue, 1], c="b")
# ax.scatter(Y[red, 0], Y[red, 1], c="r")
# ax.scatter(X[yellow, 0], X[yellow, 1], c="y")
# ax.xaxis.set_major_formatter(NullFormatter())
# ax.yaxis.set_major_formatter(NullFormatter())
ax.axis("tight")

plt.show()
