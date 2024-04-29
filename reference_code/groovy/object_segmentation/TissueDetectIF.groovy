//README
//This assumes you are running on a slide without any annotations on it


import qupath.lib.regions.*
import qupath.imagej.tools.IJTools
import qupath.imagej.gui.IJExtension
import qupath.imagej.gui.ImageJMacroRunner
import qupath.lib.plugins.parameters.ParameterList
import ij.*
import qupath.lib.objects.PathTileObject
import qupath.lib.roi.RectangleROI
import qupath.lib.scripting.QP

IJExtension.getImageJInstance()

// Create a macro runner so we can check what the parameter list contains
clearDetections();
def params = new ImageJMacroRunner(getQuPath()).getParameterList()
print ParameterList.getParameterListJSON(params, ' ')

// Change the value of a parameter, using the JSON to identify the key
params.getParameters().get('downsampleFactor').setValue(10.0 as double)
params.getParameters().get('sendOverlay').setValue(false)
params.getParameters().get('clearObjects').setValue(true)
params.getParameters().get('getROI').setValue(true)
params.getParameters().get('getOverlay').setValue(true)
print ParameterList.getParameterListJSON(params, ' ')

// Get the macro text and other required variables
//def macro = 'print("Overlay size: " + Overlay.size)'

def macro = '''
run("Split Channels");
//close();
//close();
//close();
run("Gaussian Blur...", "sigma=3");
//setAutoThreshold("MaxEntropy dark");
//run("Threshold...");
setThreshold(10, 125);
setOption("BlackBackground", true);
run("Convert to Mask");
run("Close-");
run("Fill Holes");
run("Dilate");
run("Smooth");
run("Gaussian Blur...", "sigma=10");
//setAutoThreshold("Default dark");
//run("Threshold...");
setThreshold(80, 255);
run("Convert to Mask");
//run("Dilate");
//run("Close");
run("Fill Holes");
run("Analyze Particles...", "size=500000-Infinity show=[Overlay Masks]");

//detections will already be added, uncommenting the following line will add annotation objects as well
//run("Send Overlay to QuPath", "choose_object_type=Annotation include_measurements");
'''

//Actual run part of this script

def imageData = getCurrentImageData()


// create whole slide annotation
createSelectAllObject(true); 
//selectAnnotations(); //it should select automatically so leave this commented

//reduce size of annotation to remove edge artifacts and reduce area
runPlugin('qupath.lib.plugins.objects.DilateAnnotationPlugin', '{"radiusMicrons": -200,  "lineCap": "Round",  "removeInterior": false,  "constrainToParent": true}');

objects = getAnnotationObjects()
object = objects[1] //objects[0] will be whole slide annotation, objects[1] should select inner
//create new DETECTION object(s) of tissue outline using macro
ImageJMacroRunner.runMacro(params, imageData, null, object, macro)

//Delete the annotation objects
print("Deleting annotations");
clearAnnotations();

//convert tissue newly-created tissue detection to an annotation
print("Converting detections to annotations");
selectObjects { p -> p.getPathClass() == null && p.isDetection() && p.getROI().getArea() > 1000 }
detections = getSelectedObjects()

// Create corresponding annotations (name this however you like)
def classification = getPathClass('Annotation')
def annotations = detections.collect {
new qupath.lib.objects.PathAnnotationObject(it.getROI(), classification)
}

//Remove IJ detection objects and replace with annotation objects (with same ROI points)
removeObjects(detections , true)
addObjects(annotations)
fireHierarchyUpdate()

print 'Done!'
