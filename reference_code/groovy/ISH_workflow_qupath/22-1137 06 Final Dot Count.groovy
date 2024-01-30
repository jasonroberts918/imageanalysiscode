resolveHierarchy()
selectCells();
cells = getSelectedObjects();
for (cell in cells)    {
    length = cell.getChildObjects().size()
    cell.getMeasurementList().putMeasurement("FinalDotCount", length)
}