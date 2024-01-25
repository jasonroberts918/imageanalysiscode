import qupath.lib.objects.classes.PathClass
import qupath.lib.objects.classes.PathClassFactory
//this script is for if you already ran a classifier (e.g. "cells" vs "excluded")
//and want to just run a subset on one class (just "cells" in this case)

def key = "Cell: Channel 3 mean"
def key2 = "Cytoplasm: Channel 3 mean"
def key3 = "Nucleus: Channel 3 mean"
def key4 = "Cell: Channel 3 std dev"
def key5 = "Cytoplasm: Channel 1 mean"
def key6 = "Nucleus: Channel 1 mean"


def Excluded = PathClassFactory.getPathClass("Cell")
def Excluded2 = PathClassFactory.getPathClass("Junk")

for (cell in getCellObjects()){

   def value = cell.getMeasurementList().getMeasurementValue(key)
   def value2 = cell.getMeasurementList().getMeasurementValue(key2)
   def value3 = cell.getMeasurementList().getMeasurementValue(key3)
   def value4 = cell.getMeasurementList().getMeasurementValue(key4)
   def value5 = cell.getMeasurementList().getMeasurementValue(key5)
   def value6 = cell.getMeasurementList().getMeasurementValue(key6)
   
	if (value > 50 && value2 > 40 && value3 > 75) 
	    cell.setPathClass(Excluded2)
	if (value > 50 && value2 > 30 && value3 > 50 && value4 < 20)
	    cell.setPathClass(Excluded2)
	if (value5 > 50 && value6 > 50)
	    cell.setPathClass(Excluded2)
	
	
}

fireHierarchyUpdate()
print("Done!")
