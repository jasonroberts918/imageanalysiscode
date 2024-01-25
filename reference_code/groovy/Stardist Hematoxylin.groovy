import qupath.lib.images.servers.*
import qupath.tensorflow.stardist.StarDist2D

selectAnnotations();
// Specify the model file (you will need to change this!)
var pathModel = "C:\\Analysis_Studies\\Stardist Scripts\\dsb2018_heavy_augment"

var stardist = StarDist2D.builder(pathModel)
        .threshold(0.3)              // Probability (detection) threshold
        .channels(ColorTransforms.createColorDeconvolvedChannel(getCurrentImageData().getColorDeconvolutionStains(), 1))            // Select detection channel
        .normalizePercentiles(1, 99) // Percentile normalization
        .pixelSize(0.3)              // Resolution for detection
        .cellExpansion(10.0)          // Approximate cells based upon nucleus expansion
        .measureShape()              // Add shape measurements
        .measureIntensity()          // Add cell measurements (in all compartments)
        .includeProbability(true)    // Add probability as a measurement (enables later filtering)
        .build()
        
selectAnnotations();

// Run detection for the selected objects
var imageData = getCurrentImageData()
var pathObjects = getSelectedObjects()
if (pathObjects.isEmpty()) {
    Dialogs.showErrorMessage("StarDist", "Please select a parent object!")
    return
}
stardist.detectObjects(imageData, pathObjects)
println 'Done!'