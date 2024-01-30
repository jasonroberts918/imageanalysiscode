anos = getAnnotationObjects()
for (ano in anos){
    selectObjects(ano)
    runPlugin('qupath.lib.plugins.objects.DilateAnnotationPlugin', '{"radiusMicrons": -200.0,  "lineCap": "Round",  "removeInterior": false,  "constrainToParent": false}');
    resolveHierarchy();
    fireHierarchyUpdate();
    //delete original annotation
    selectObjects(ano);
    clearSelectedObjects(true);
    print(ano)}
    
//delete all cells not within new annotation
selectObjects{p -> (p.getLevel()==1) && (p.isAnnotation() == false)};
clearSelectedObjects(false);

print('done')
