import qupath.lib.regions.*
import qupath.imagej.tools.IJTools
import qupath.imagej.gui.IJExtension
import qupath.imagej.gui.ImageJMacroRunner
import qupath.lib.plugins.parameters.ParameterList
import ij.*

IJExtension.getImageJInstance()

// Create a macro runner so we can check what the parameter list contains
clearDetections();
def params = new ImageJMacroRunner(getQuPath()).getParameterList()
print ParameterList.getParameterListJSON(params, ' ')

// Change the value of a parameter, using the JSON to identify the key
params.getParameters().get('downsampleFactor').setValue(3.0 as double)
params.getParameters().get('sendOverlay').setValue(false)
params.getParameters().get('clearObjects').setValue(true)
params.getParameters().get('getROI').setValue(true)
params.getParameters().get('getOverlay').setValue(true)
print ParameterList.getParameterListJSON(params, ' ')

// Get the macro text and other required variables
//def macro = 'print("Overlay size: " + Overlay.size)'

def macro = '''
run("Clear Results");

run("Split Channels");
close();
run("Gaussian Blur...", "sigma=1.2");
run("Subtract Background...", "rolling=2");
run("Sharpen");
run("Find Edges");
//run("Gaussian Blur...", "sigma=1.2");

run("Threshold...");
setThreshold(4, 255);

run("Convert to Mask");
run("Close");
run("Despeckle");
run("Erode");
//run("Dilate");
run("Invert");
//run("Adjustable Watershed", "tolerance=0.2");
run("Set Measurements...", "area mean standard modal min shape skewness centroid perimeter add redirect=None decimal=3");
run("Analyze Particles...", "size=100-20000 circularity=0.00-1.00 show=Overlay Masks add");

//detections will already be added, uncommenting the following line will add annotation objects as well
//run("Send Overlay to QuPath", "choose_object_type=Annotation include_measurements");
'''

def imageData = getCurrentImageData()
selectAnnotations();
objects = getSelectedObjects()
for (object in objects) {
ImageJMacroRunner.runMacro(params, imageData, null, object, macro)
}

print 'Done!' 
