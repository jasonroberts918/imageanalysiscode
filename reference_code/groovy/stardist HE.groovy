import qupath.tensorflow.stardist.StarDist2D
import qupath.lib.images.servers.*

//selectAnnotations();
// Specify the model directory (you will need to change this!)
def pathModel = 'C:/Analysis_Studies/Stardist Scripts/he_heavy_augment/'

//runPlugin('qupath.imagej.detect.tissue.SimpleTissueDetection2', '{"threshold": 240,  "requestedPixelSizeMicrons": 20.0,  "minAreaMicrons": 100000.0,  "maxHoleAreaMicrons": 1000000.0,  "darkBackground": false,  "smoothImage": true,  "medianCleanup": true,  "dilateBoundaries": false,  "smoothCoordinates": true,  "excludeOnBoundary": false,  "singleAnnotation": false}');

def stardist = StarDist2D.builder(pathModel)
      .threshold(0.3)              // Prediction threshold
      .normalizePercentiles(1, 99) // Percentile normalization
      .pixelSize(0.35)              // Resolution for detection
      .cellExpansion(5.0)
      .measureShape()              // Add shape measurements
      .measureIntensity()  
      .build()

def imageData = getCurrentImageData()
    selectCells();
    clearSelectedObjects(true);
    clearSelectedObjects();
    selectTiles();
    //selectObjects(List)
    //annotations = getSelectedObjects()
    //for (item in list) {
        //selectObjects(item)
        //selectAnnotations()
        def pathObjects = getSelectedObjects()
        
        if (pathObjects.isEmpty()) {
              Dialogs.showErrorMessage("StarDist", "Please select a parent object!")
              return
        }
        
        stardist.detectObjects(imageData, pathObjects)
        
        javafx.application.Platform.runLater {
            getCurrentViewer().getImageRegionStore().cache.clear()
            System.gc()
        }
    //}
println 'Done!'