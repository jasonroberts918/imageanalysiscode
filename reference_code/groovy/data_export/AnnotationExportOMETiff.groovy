def imageData = getCurrentImageData()
//print(imageData)
//def server = imageData.getServer()
def server = getCurrentServer()
//print(server)
def entry = getProjectEntry()
print(entry)
def name = entry.getImageName()[0..-6] //remove .mrxs extension
def extension = ".ome.tif"
def path = buildFilePath(PROJECT_BASE_DIR, name + extension)
print(path)

//should just have one annotations around the tissue of interest (smaller is better)
selectAnnotations()
def roi = getSelectedObjects()[0].getROI()
def requestROI = RegionRequest.createInstance(server.getPath(), 1, roi) //downsample 1 = full res
writeImageRegion(server, requestROI, path)
