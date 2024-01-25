//The resulting jsons will be exported to a folder called Centroids
out_dir = 'Centroids'
//All cells belonging to the class names included in "terms" will be added to the json
terms = ["Positive"] 

def imageData = QPEx.getCurrentImageData()
def imageName = GeneralTools.getNameWithoutExtension(imageData.getServer().getMetadata().getName())
print(imageName)

def pathOutput = buildFilePath(PROJECT_BASE_DIR, out_dir)
mkdirs(pathOutput)
def filename = buildFilePath(PROJECT_BASE_DIR, out_dir, imageName + '.json')
def file = new File(filename)

cells = getDetectionObjects().findAll({p -> (p.getPathClass().toString() in terms)})
list = []

for (cell in cells) {
    cell = [
        "Class": cell.getPathClass().toString(),
        "x": cell.ROI.getCentroidX(),
        "y": cell.ROI.getCentroidY()
    ]
    list.add(cell)
}

boolean prettyPrint = true
def gson = GsonTools.getInstance(prettyPrint)
file << gson.toJson(list) << System.lineSeparator()
