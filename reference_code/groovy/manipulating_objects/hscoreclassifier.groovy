// Delete objects that do not have a nucleus
//def noNuclei = getCellObjects().findAll {it.getNucleusROI() == null}
//removeObjects(noNuclei, true)

resetDetectionClassifications();

high = getPathClass('high')
medium = getPathClass('medium')
low = getPathClass('low')
negative = getPathClass('negative')
//other = getPathClass('other')

for (cell in getCellObjects()) {
    ch1 = measurement(cell, 'DAB: Nucleus: Mean')

    if (ch1 > 1.105) 
        cell.setPathClass(high)
        
    if (ch1 > 0.872 && ch1 <=1.105)
        cell.setPathClass(medium)
    
    if (ch1 > 0.604 && ch1 <=0.872)
        cell.setPathClass(low)
    
    if (ch1 <= 0.604)
        cell.setPathClass(negative)
}
fireHierarchyUpdate()
