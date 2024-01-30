import static qupath.lib.gui.scripting.QPEx.*
import com.google.gson.Gson
import qupath.lib.geom.Point2
import qupath.lib.objects.PathAnnotationObject
import qupath.lib.roi.PolygonROI


//String text = new File("C:\\Analysis_Studies\\20-493 Grace\\Qupath\\ano_points\\20-493_Grace_NGLY-1_1004-16.mrxs.json").text
//print(text)

def txtDir = buildFilePath(QPEx.PROJECT_BASE_DIR, 'DRG')   
print(txtDir)                          
def imageName = getProjectEntry().getImageName() + '.json'                                           
def AnoFile_name = buildFilePath(txtDir, imageName)
String name = AnoFile_name
String text = new File(AnoFile_name).getText()

//telling gson library that json (text) is an array of m        aps ("this json file is an array of json objects")
def annotations = new Gson().fromJson(text, Map[].class)


//Convert to QuPath annotations
def output = []
for (annotation in annotations) {
    def pathJson = new Gson().toJson(annotation.geometry);
    def poly = new Gson().fromJson(pathJson, Map)
    def polyName = annotation.properties.classification.name
    print(polyName)
    def points = poly.coordinates[0].collect {new Point2(it[0], it[1])}
    def polygon = new PolygonROI(points)
    def pathAnnotation = new PathAnnotationObject(polygon)
    pathAnnotation.setName(polyName)
    output << pathAnnotation
}

// Add to current hierarchy
QPEx.addObjects(output)
