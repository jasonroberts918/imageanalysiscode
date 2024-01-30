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
//runPlugin('qupath.lib.algorithms.TilerPlugin', '{"tileSizeMicrons": 2000.0,  "trimToROI": true,  "makeAnnotations": true,  "removeParentAnnotation": true}');
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
run("Options...", "iterations=1 count=1 do=Nothing");
run("Options...", "iterations=1 count=1 black");
setOption("BlackBackground", false);
run("Make Binary");
//run invert for blocks where original method fails
run("Invert");
run("Despeckle");
run("Despeckle");
run("Analyze Particles...", "size=0-2500 show=[Overlay Masks] add");
'''

//Actual run part of this script

def imageData = getCurrentImageData()
selectAnnotations();
objects = getAnnotationObjects()

for (o in objects){
    ImageJMacroRunner.runMacro(params, imageData, null, o, macro)
    }

fireHierarchyUpdate()

print 'Done!'

*/
