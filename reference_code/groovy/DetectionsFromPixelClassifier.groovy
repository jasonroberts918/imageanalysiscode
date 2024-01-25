import qupath.lib.gui.ml.PixelClassifierTools

//Need a full image annotation to begin with
selectAnnotations();
def annotations = getSelectedObjects()

//Define pixel classifier
def project = getProject()
def classifier = project.getPixelClassifiers().get('Takeda Fibrosis')

//Define image data
def imageData = getCurrentImageData()

//Convert pixel classifier to annotations
//Not sure if the smallest annotations/holes is in pixels or microns....
PixelClassifierTools.createDetectionsFromPixelClassifier(imageData, classifier, annotations, 10, 10, false, true)
