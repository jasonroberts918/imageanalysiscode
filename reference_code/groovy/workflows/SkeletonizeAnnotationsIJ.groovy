//Note: this script requires the AnalyzeSkeleton IJ plugin to be in your extensions directory before running

import qupath.imagej.tools.IJTools
import qupath.imagej.gui.IJExtension
import qupath.imagej.gui.ImageJMacroRunner

params = new ImageJMacroRunner(getQuPath()).getParameterList()

// Change the value of a parameter, using the JSON to identify the key
params.getParameters().get('downsampleFactor').setValue(2)
params.getParameters().get('sendROI').setValue(true)
params.getParameters().get('sendOverlay').setValue(false)
params.getParameters().get('getOverlay').setValue(false)
params.getParameters().get('getROI').setValue(false)
params.getParameters().get('clearObjects').setValue(false)

//new ImageJ macro
macro = """run("ROI Manager...");
roiManager("Add");
run("Create Mask");
selectWindow("Mask");
run("Skeletonize");
run("Analyze Skeleton (2D/3D)", "prune=none");

numBranches="# Branches:" + getResult("# Branches", 0);
numJunctions="# Junctions:" + getResult("# Junctions", 0);
aveBranchLength="Average Branch Length:" + getResult("Average Branch Length", 0);
maxBranchLength="Maximum Branch Length:" + getResult("Maximum Branch Length", 0);

measurements=numBranches +","+ numJunctions +","+ aveBranchLength +","+ maxBranchLength
roiManager("Select", 0);
roiManager("Rename", measurements);

selectWindow("Dermis");
run("Set Measurements...", "area modal display add redirect=None decimal=3");
run("From ROI Manager");

run("Send Overlay to QuPath", "choose_object_type=Detection include_measurements");
run("Close All");
roiManager("Deselect");
roiManager("Delete");

"""

def imageData = getCurrentImageData()
def annotations = getAnnotationObjects().findAll{it.getPathClass().toString()=="Dermis"}

// Loop through the annotations and run the macro
for (annotation in annotations) {
    ImageJMacroRunner.runMacro(params, imageData, null, annotation, macro)

    vesseldet=getDetectionObjects()
    List<String[]> measurements = vesseldet[0].getName().split(",") //Assumes there is only 1 detection!
    for (measurement in measurements) {
        def (header, data) = measurement.split(":")
        annotation.getMeasurementList().putMeasurement(header,data as double)
    }
    clearDetections();
}
