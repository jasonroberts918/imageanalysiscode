RandomRegion = getAnnotationObjects().findAll{it.getPathClass() == getPathClass("Region*")}
RandomRegion.each{anno->
    CellsinRandomRegion = getCurrentHierarchy().getObjectsForROI(qupath.lib.objects.PathDetectionObject, anno.getROI())
}
CellsinRandomRegion.each{cell->
    getCurrentHierarchy().getSelectionModel().setSelectedObject(cell, true);
}
clearSelectedObjects()

//Delete annotation by class
selectObjectsByClassification("Region*");
clearSelectedObjects(true);
clearSelectedObjects();
