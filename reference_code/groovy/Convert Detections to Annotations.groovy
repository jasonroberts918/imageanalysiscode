import qupath.lib.objects.PathAnnotationObject

// Create new annotations with the same ROIs and classifications as the detections
def detections = getDetectionObjects()
def newAnnotations = detections.collect {detection -> new PathAnnotationObject(detection.getNucleusROI(), detection.getPathClass())}

// Remove the detections, add the annotations
addObjects(newAnnotations)