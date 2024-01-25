import qupath.ext.stardist.StarDist2D
import qupath.tensorflow.stardist.StarDist2D
import qupath.lib.images.servers.*

selectAnnotations();
// Specify the model .pb file (you will need to change this!)
def pathModel =  'C:/Program Files/QuPath-0.2.3_stardist/stardist models/he_heavy_augment/'

def stardist = StarDist2D.builder(pathModel)
      .threshold(0.01)              // Prediction threshold
      .normalizePercentiles(1, 99) // Percentile normalization
      .pixelSize(0.3)              // Resolution for detection
      .cellExpansion(10.0)          // Approximate cells based upon nucleus expansion
      .cellConstrainScale(1.5)     // Constrain cell expansion using nucleus size
      .measureShape()              // Add shape measurements
      .measureIntensity()          // Add cell measurements (in all compartments)
      .build()

// Run detection for the selected objects
def imageData = getCurrentImageData()
def pathObjects = getSelectedObjects()
if (pathObjects.isEmpty()) {
    Dialogs.showErrorMessage("StarDist", "Please select a parent object!")
    return
}
stardist.detectObjects(imageData, pathObjects)
println 'Done!'