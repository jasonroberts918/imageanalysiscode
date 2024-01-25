clearDetections();
selectAnnotations();
//a negative radius will shrink the annotation, positive will expand
runPlugin('qupath.lib.plugins.objects.DilateAnnotationPlugin', '{"radiusMicrons": -250.0,  "removeInterior": false,  "constrainToParent": true}');

//the following line selects only the outer annotation and deletes it
selectObjects{p -> (p.getLevel()==1) && (p.isAnnotation()==true)};
clearSelectedObjects(true);

////set desired stain vector and run analysis (need to run separately)
//setColorDeconvolutionStains('{"Name" : "DAB Dark", "Stain 1" : "Hematoxylin", "Values 1" : "0.65111 0.70119 0.29049 ", "Stain 2" : "DAB", "Values 2" : "0.38866 0.66122 0.64166 ", "Background" : " 250 251 248 "}');
//selectAnnotations();
//runPlugin('qupath.imagej.detect.tissue.PositivePixelCounterIJ', '{"downsampleFactor": 2,  "gaussianSigmaMicrons": 1.5,  "thresholdStain1": 0.4,  "thresholdStain2": 1.0,  "addSummaryMeasurements": true}');
