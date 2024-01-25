import qupath.lib.objects.classes.PathClass
import qupath.lib.objects.classes.PathClassFactory


def key = "Nucleus: Hematoxylin OD mean"
def key2 = "Nucleus: DAB OD mean"
def key3 = "Cytoplasm: DAB OD mean"
def key4 = "Nucleus: Channel 2 mean"


def Excluded = PathClassFactory.getPathClass("Positive")
def Excluded2 = PathClassFactory.getPathClass("Negative")
def Excluded3 = PathClassFactory.getPathClass("Junk")



for (cell in getCellObjects()){
   def value = cell.getMeasurementList().getMeasurementValue(key)
   def value2 = cell.getMeasurementList().getMeasurementValue(key2)
    def value3 = cell.getMeasurementList().getMeasurementValue(key3)
    def value4 = cell.getMeasurementList().getMeasurementValue(key4)
    
    
	if (value > 85 && value2 > 40 && value < 150 && value3 > 20 && value4 < 115) 
	    cell.setPathClass(Excluded)
	if (value < 85 && value2 > 40 || value > 150 || value3 < 20 || value4 > 115)
	    cell.setPathClass(Excluded2)
	if (value2 < 40)
	    cell.setPathClass(Excluded3)
	
}

fireHierarchyUpdate()
print("Done!")
