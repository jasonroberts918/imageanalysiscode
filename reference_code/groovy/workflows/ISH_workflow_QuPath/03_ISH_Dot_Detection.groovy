selectCells();
runPlugin('qupath.imagej.detect.cells.SubcellularDetection', '{"detection[ISH Dots]": 0.1,  "doSmoothing": false,  "splitByIntensity": true,  "splitByShape": true,  "spotSizeMicrons": 1.0,  "minSpotSizeMicrons": 0.06,  "maxSpotSizeMicrons": 5.0,  "includeClusters": true}');
