import qupath.lib.roi.*
import qupath.lib.objects.PathAnnotationObject
import qupath.lib.objects.classes.PathClassFactory
import qupath.lib.objects.PathObject

def oldClass = PathClassFactory.getPathClass("Positive")
def newClass = PathClassFactory.getPathClass("None")


getAnnotationObjects().findAll{
    if (it.getPathClass() == oldClass)
        it.setPathClass(newClass)
    else
        print("Not reclassing: " + it.getPathClass())
}

