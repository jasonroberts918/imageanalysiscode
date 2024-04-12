// Get all detections that are NOT cells
def toDelete = getObjects({p -> p.isDetection() == true && p.isCell() == false})

// And gone!
removeObjects(toDelete, true)

println("Done!")