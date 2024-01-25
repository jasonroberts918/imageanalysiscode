// QP 0.2.3
AREA_THRESHOLD = 12

def server = getCurrentServer()
def pixelWidth = server.getMetadata().getPixelCalibration()getPixelWidthMicrons()
def pixelHeight = server.getMetadata().getPixelCalibration()getPixelHeightMicrons()

def smallDetections = getDetectionObjects().findAll {it.getROI().getScaledArea(pixelWidth, pixelHeight) < AREA_THRESHOLD}
removeObjects(smallDetections, true)