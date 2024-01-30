//Useful if you are trimming an annotation after having generated detections, and want a quick way to eliminate
//cells now outside of your annotated regions.

//Edit annotation first then select it and resolve hierarchy so objects are inside your annotation
selectAnnotations();
resolveHierarchy()

selectObjects{p -> (p.getLevel()==1) && (p.isAnnotation() == false)};
clearSelectedObjects(false);

//selectAnnotations();
//resolveHierarchy()m m
