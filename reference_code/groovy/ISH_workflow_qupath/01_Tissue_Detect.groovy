import static qupath.lib.gui.scripting.QPEx.*
import ij.*
import ij.measure.Calibration
import ij.plugin.filter.ThresholdToSelection
import ij.process.ByteProcessor
import ij.process.ImageProcessor

import qupath.imagej.tools.IJTools
import qupath.lib.roi.*
import qupath.lib.objects.PathAnnotationObject
import qupath.lib.objects.classes.PathClassFactory
import qupath.opencv.tools.OpenCVTools

import qupath.lib.regions.*
import qupath.lib.images.ImageData
import qupath.lib.images.servers.ServerTools
import qupath.lib.objects.PathObject
import qupath.lib.plugins.parameters.ParameterList

import static org.bytedeco.opencv.global.opencv_core.bitwise_not
import static org.bytedeco.opencv.global.opencv_core.subtract
import static org.bytedeco.opencv.global.opencv_imgproc.CHAIN_APPROX_SIMPLE
import static org.bytedeco.opencv.global.opencv_imgproc.CHAIN_APPROX_NONE
import static org.bytedeco.opencv.global.opencv_imgproc.COLOR_BGR2GRAY
import static org.bytedeco.opencv.global.opencv_imgproc.Canny
import static org.bytedeco.opencv.global.opencv_imgproc.GaussianBlur
import static org.bytedeco.opencv.global.opencv_imgproc.MORPH_DILATE
import static org.bytedeco.opencv.global.opencv_imgproc.MORPH_ERODE
import static org.bytedeco.opencv.global.opencv_imgproc.MORPH_CLOSE
import static org.bytedeco.opencv.global.opencv_imgproc.MORPH_OPEN
import static org.bytedeco.opencv.global.opencv_imgproc.MORPH_TOPHAT
import static org.bytedeco.opencv.global.opencv_imgproc.MORPH_ELLIPSE
import static org.bytedeco.opencv.global.opencv_imgproc.MORPH_RECT
import static org.bytedeco.opencv.global.opencv_imgproc.RETR_TREE
import static org.bytedeco.opencv.global.opencv_imgproc.RETR_EXTERNAL
import static org.bytedeco.opencv.global.opencv_imgproc.THRESH_BINARY
import static org.bytedeco.opencv.global.opencv_imgproc.THRESH_OTSU
import static org.bytedeco.opencv.global.opencv_imgproc.createCLAHE
import static org.bytedeco.opencv.global.opencv_imgproc.cvtColor
import static org.bytedeco.opencv.global.opencv_imgproc.findContours
import static org.bytedeco.opencv.global.opencv_imgproc.fillPoly
import static org.bytedeco.opencv.global.opencv_imgproc.getStructuringElement
import static org.bytedeco.opencv.global.opencv_imgproc.morphologyEx
import static org.bytedeco.opencv.global.opencv_imgproc.threshold
import static org.bytedeco.opencv.global.opencv_imgproc.connectedComponentsWithStats

import org.bytedeco.opencv.opencv_core.Mat
import org.bytedeco.opencv.opencv_core.MatVector
import org.bytedeco.opencv.opencv_core.Scalar
import org.bytedeco.opencv.opencv_core.Size
import org.bytedeco.opencv.opencv_imgproc.CLAHE

def MAX_KERNEL_SIZE = 20 // MIN_PARTICLE_AREA = 400

def pixelSizeMicrons = 20
def downsample = 20
def server = getCurrentServer()
def path = server.getPath()

def cal_init = server.getPixelCalibration()
//if (cal_init.hasPixelSizeMicrons()) {
//downsample = pixelSizeMicrons / cal_init.getAveragedPixelSizeMicrons()
//}

print("downsample " + downsample.toString())

def request = RegionRequest.createInstance(path, downsample, 0, 0, server.getWidth(), server.getHeight())
def bufimg = server.readBufferedImage(request)

Mat tissueMask = OpenCVTools.imageToMat(bufimg)

// extract structure map
cvtColor(tissueMask, tissueMask, COLOR_BGR2GRAY)
bitwise_not(tissueMask, tissueMask)

CLAHE clahe = createCLAHE()
clahe.setClipLimit(3.0)
clahe.setTilesGridSize(new Size(32, 32))
clahe.apply(tissueMask, tissueMask)

Canny(tissueMask, tissueMask, 60, 180)

GaussianBlur(tissueMask, tissueMask, new Size(1, 1), 2)
threshold(tissueMask, tissueMask, 0, 255, THRESH_BINARY + THRESH_OTSU)

// remove horizontal and vertical lines from partial scans (CZI) TODO make optional
Mat horizontal = tissueMask.clone()
Mat vertical = tissueMask.clone()
Mat hor_kernel = getStructuringElement(MORPH_RECT, new Size((tissueMask.cols() / 60).intValue(), 1))
Mat ver_kernel = getStructuringElement(MORPH_RECT, new Size(1, (tissueMask.rows() / 60).intValue()))

Mat temp = new Mat()
morphologyEx(horizontal, temp, MORPH_TOPHAT, hor_kernel)
subtract(horizontal, temp, horizontal)
morphologyEx(vertical, temp, MORPH_TOPHAT, ver_kernel)
subtract(vertical, temp, vertical)

Mat kernel3 = getStructuringElement(MORPH_ELLIPSE, new Size(3, 3))
morphologyEx(horizontal, horizontal, MORPH_DILATE, kernel3)
morphologyEx(vertical, vertical, MORPH_DILATE, kernel3)

MatVector contours = new MatVector()
Mat hierarchy = new Mat()

bitwise_not(tissueMask, tissueMask)
findContours(horizontal, contours, hierarchy, RETR_TREE, CHAIN_APPROX_NONE)
fillPoly(tissueMask, contours, Scalar.WHITE)
findContours(vertical, contours, hierarchy, RETR_TREE, CHAIN_APPROX_NONE)
fillPoly(tissueMask, contours, Scalar.WHITE)
bitwise_not(tissueMask, tissueMask)


// clean up mask
Mat kernel7 = getStructuringElement(MORPH_ELLIPSE, new Size(7, 7))
morphologyEx(tissueMask, tissueMask, MORPH_CLOSE, kernel7)
Mat kernel11 = getStructuringElement(MORPH_ELLIPSE, new Size(11, 11))
morphologyEx(tissueMask, tissueMask, MORPH_DILATE, kernel11)

def imp = OpenCVTools.matToImagePlus(tissueMask, "image")
IJTools.calibrateImagePlus(imp, request, server)
imp.show()
// detect outer contour of tissue:
findContours(tissueMask, contours, hierarchy, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
fillPoly(tissueMask, contours, new Scalar(255))

// get area info of tissue fragments
Mat labels = new Mat()
Mat stats = new Mat()
Mat centroids = new Mat()
connectedComponentsWithStats(tissueMask, labels, stats, centroids, 8, 4) // CV_32S 4
List labelAreas = new ArrayList<>()
for (int i=1; i < stats.rows(); i++) {
labelAreas.add(stats.getIntBuffer().get(i*5+4)) // row + n_cols + CC_STAT_AREA = 4
}

println("max area " + labelAreas.max().toString())
println("mean area " + labelAreas.average() )
println("particle areas " + labelAreas.sort().reverse().toString())
println("sum of areas " + labelAreas*.value.sum().toString())

def sum_area = labelAreas*.value.sum()
labelAreas = labelAreas.sort().reverse()

def sum = 0
def j = 0
for(int i=0; i < labelAreas.size()-1; i++) {
sum += labelAreas[i]
if(sum > 0.85 * sum_area) {
j = i + 1
break
}
}
println("sum 85% " + sum.toString())
println("next particle area " + labelAreas[j].toString())

//def largeKernelSize = (int)Math.ceil(Math.sqrt((double)labelAreas[j]))
//if(largeKernelSize > MAX_KERNEL_SIZE) {
//largeKernelSize = MAX_KERNEL_SIZE
//}
//

largeKernelSize = 100

println("kernel size to remove small tissue fragments " + largeKernelSize.toString())

// remove small tissue fragments and expand mask a little bit
Mat largeKernel = getStructuringElement(MORPH_ELLIPSE, new Size(largeKernelSize, largeKernelSize))
morphologyEx(tissueMask, tissueMask, MORPH_OPEN, largeKernel)
morphologyEx(tissueMask, tissueMask, MORPH_DILATE, kernel7)

ImagePlus impNew = OpenCVTools.matToImagePlus(tissueMask, "mask")

// clean-up
tissueMask.release()
kernel7.release()
kernel3.release()
largeKernel.release()
horizontal.release()
vertical.release()
hor_kernel.release()
ver_kernel.release()
labels.release()
centroids.release()
stats.release()

def bp = impNew.getProcessor().convertToByteProcessor()
def cal = impNew.getCalibration()

// Create a classification, if necessary
def classificationString = "None"
def pathClass = null
if (classificationString != 'None')
pathClass = PathClassFactory.getPathClass(classificationString)

// To create the ROI, travel into ImageJ
bp.setThreshold(127.5, Double.MAX_VALUE, ImageProcessor.NO_LUT_UPDATE)
def roiIJ = new ThresholdToSelection().convert(bp)

int z = 0
int t = 0
def plane = ImagePlane.getPlane(z, t)

// Convert ImageJ ROI to a QuPath ROI
// This assumes we have a single 2D image (no z-stack, time series)
def roi = IJTools.convertToROI(roiIJ, cal, downsample, plane)

def annotation = new PathAnnotationObject(roi, pathClass)
addObject(annotation)

println("done")
