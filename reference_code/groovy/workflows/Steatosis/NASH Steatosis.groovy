//README
//This assumes you are running on a slide with a whole tissue or tiled whole tissue annotation
import qupath.lib.regions.*
import qupath.imagej.tools.IJTools
import qupath.imagej.gui.IJExtension
import qupath.imagej.gui.ImageJMacroRunner
import qupath.lib.plugins.parameters.ParameterList
import ij.*
import qupath.lib.objects.PathTileObject
import qupath.lib.roi.RectangleROI
import qupath.lib.scripting.QP


selectAnnotations();
runPlugin('qupath.lib.algorithms.TilerPlugin', '{"tileSizeMicrons": 1000.0,  "trimToROI": true,  "makeAnnotations": true,  "removeParentAnnotation": false}');
runPlugin('qupath.lib.plugins.objects.SplitAnnotationsPlugin', '{}');
resetSelection();


selectAnnotations();
runPlugin('qupath.lib.algorithms.TilerPlugin', '{"tileSizeMicrons": 1000.0,  "trimToROI": true,  "makeAnnotations": true,  "removeParentAnnotation": true}');
runPlugin('qupath.lib.plugins.objects.SplitAnnotationsPlugin', '{}');
resetSelection();


// Create a macro runner so we can check what the parameter list contains
IJExtension.getImageJInstance()
def params = new ImageJMacroRunner(getQuPath()).getParameterList()
print ParameterList.getParameterListJSON(params, ' ')

// Change the value of a parameter, using the JSON to identify the key
params.getParameters().get('downsampleFactor').setValue(1.0 as double)
params.getParameters().get('sendOverlay').setValue(false)
params.getParameters().get('clearObjects').setValue(true)
params.getParameters().get('getROI').setValue(true)
params.getParameters().get('getOverlay').setValue(true)
print ParameterList.getParameterListJSON(params, ' ')

def macro = '''
run("Split Channels");
close();
run("Duplicate...", "title=Green");
run("Duplicate...", "title=Dev");
run("Variance...", "radius=0.5");
selectWindow("Green");
imageCalculator("Subtract create", "Green","Dev");
selectWindow("Result of Green");
run("Smooth");
run("Threshold...");
setThreshold(0, 210);
setOption("BlackBackground", false);
run("Convert to Mask");

//run("Despeckle");
//run("Erode");
//run("Despeckle");
//run("Dilate");

run("Invert");
run("Fill Holes");
run("Dilate");
run("Close-");
run("Watershed");

run("Analyze Particles...", "size=0-4000 show=[Overlay Masks] add");
'''

//Actual run part of this script
clearDetections();
def imageData = getCurrentImageData()
//selectAnnotations();
objects = getAnnotationObjects()

for (o in objects){
    ImageJMacroRunner.runMacro(params, imageData, null, o, macro)
    }

fireHierarchyUpdate()

//delete duplicates -- artifact of IJ workflow with tiles
//badParentName = "White Blob"

//toRemove = getDetectionObjects().findAll{it.getParent().toString().contains(badParentName)}
//removeObjects(toRemove, true)

//add measurements to remaining objects
selectDetections();
addShapeMeasurements("LENGTH", "CIRCULARITY", "SOLIDITY", "MAX_DIAMETER", "MIN_DIAMETER")
runPlugin('qupath.lib.algorithms.IntensityFeaturesPlugin', '{"pixelSizeMicrons": 2.0,  "region": "ROI",  "tileSizeMicrons": 10.0,  "colorOD": true,  "colorStain1": true,  "colorStain2": true,  "colorStain3": false,  "colorRed": false,  "colorGreen": false,  "colorBlue": false,  "colorHue": true,  "colorSaturation": true,  "colorBrightness": true,  "doMean": true,  "doStdDev": true,  "doMinMax": true,  "doMedian": true,  "doHaralick": false,  "haralickDistance": 1,  "haralickBins": 32}');
//more features
selectAnnotations();
runPlugin('qupath.lib.plugins.objects.SmoothFeaturesPlugin', '{"fwhmMicrons": 15.0,  "smoothWithinClasses": false}');