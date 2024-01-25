import qupath.lib.objects.classes.PathClass
import qupath.lib.objects.classes.PathClassFactory
//this script is for if you already ran a classifier (e.g. "cells" vs "excluded")
//and want to just run a subset on one class (just "cells" in this case)

def key = "Nucleus: DAB OD mean"
def key2 = "Nucleus: Hematoxylin OD mean"

def Excluded = PathClassFactory.getPathClass("Positive")
def Excluded2 = PathClassFactory.getPathClass("Negative")

def aCertainClass = getDetectionObjects().findAll {it.getPathClass().getName() == "Cells"}
for (cell in aCertainClass){
   def value = cell.getMeasurementList().getMeasurementValue(key)
   def value2 = cell.getMeasurementList().getMeasurementValue(key2)
    
	if (value> 0.4) 
	    cell.setPathClass(Excluded)
	if (value< 0.4)
	    cell.setPathClass(Excluded2)
	
}

fireHierarchyUpdate()
print("Done!")
