// Create an empty text file
def file_name = getProjectEntry().getImageName() + '.txt'
def path = buildFilePath(PROJECT_BASE_DIR, file_name)
def file = new File(path)
file.text = ''
// Loop through all objects & write the points to the file
for (detection in getAnnotationObjects()) {
    
    String clasif = detection.getPathClass()
    if (clasif != "Negative"){
    // Check for interrupt (Run -> Kill running script)
    if (Thread.interrupted())
        break
    // Get the ROI
    def roi = detection.getROI()
    //double x = roi.getCentroidX()
    //double y = roi.getCentroidY()
    if (roi == null)
        continue
   
    // Write the points; but beware areas, and also ellipses!
    file <<roi.getPolygonPoints()<< System.lineSeparator()}
}
print 'Done!'
