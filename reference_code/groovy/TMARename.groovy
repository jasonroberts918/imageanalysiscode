for (annotation in getTMACoreList())
{

   def StringName = annotation.getName()
   
   def descendantDetections = getDetectionObjects().findAll {annotation.getROI().contains(it.getROI().getCentroidX(),it.getROI().getCentroidY() )}   
   for (detection in descendantDetections)
       { 
       detection.setName(StringName)
       }
   print(annotation)
}
