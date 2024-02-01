import cv2
import openslide
import numpy as np
import os
from matplotlib import pyplot as plt
from deepgaze.color_classification import HistogramColorClassifier
from multiprocessing import Pool, freeze_support
from multiprocessing.dummy import Pool as ThreadPool

import multiprocessing

#useful function that shows an image in cv2 resized to whole image screen
def show_image(img):
    cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("window", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow("window", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def return_intersection(hist_1, hist_2):
    minima = np.minimum(hist_1, hist_2)
    intersection = np.true_divide(np.sum(minima), np.sum(hist_2))
    return intersection

def find_contours(path_to_image,dest_path,artifact_classifier,tile_size,resolution_defined):

    #my_classifier.addModelHistogram(tissue_2)

#Load image and grab the 32x downsample such that we can actually load it all into memory and visualize
    mrxs_loaded = openslide.open_slide(path_to_image)
    dims_5 = mrxs_loaded.level_dimensions[5]
    downsampled_x,downsampled_y = dims_5
    image_down_2 = np.array(mrxs_loaded.read_region((0,0),5,(downsampled_x, downsampled_y)))
    #image_down_2 = image_down_2.transpose(1,0,2)

    #Anywhere that is "black" change to white (areas of mrxs file that are not actually scanned become white)
    image_down_2 = cv2.cvtColor(image_down_2, cv2.COLOR_BGR2RGB)
    image_down_2[np.where((image_down_2==[0,0,0]).all(axis = 2))] = [255,255,255]


    # Threshold using otsu to make a binary
    img_grey = cv2.cvtColor(image_down_2, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(img_grey, 0, 255, cv2.THRESH_OTSU)
    #thresh = cv2.medianBlur(thresh,8)

    #Change the top portion of the slide to white so we don't get tripped up
    cv2.rectangle(img = thresh, pt1 = (0, 0), pt2 = (downsampled_x, 1500), color = (255, 255, 255), thickness = -1)

    #ret,thr = cv2.threshold(img_grey, 0, 255, cv2.THRESH_OTSU)

    #Filtering and blurring to get rid of noise
    kernel = np.ones((5,5),np.uint8)
    erosion = cv2.erode(thresh,kernel, iterations = 1)
    dilation = cv2.dilate(erosion, kernel, iterations = 1)
    dilation = cv2.medianBlur(dilation, 5)
    dilation = cv2.bitwise_not(dilation)

    #Finding the contours
    image, contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    #print(contours)
    cnt_final = []

    #Making sure each valid contour is >5000 pixels, can be increased?
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 5000:
            x, y, w, h = cv2.boundingRect(cnt)
            roi = image_down_2[y:y + h, x:x + w]
            comparison_array = artifact_classifier.returnHistogramComparisonArray(roi,method="intersection")
            probability_array = comparison_array / np.sum(comparison_array)
            #print(probability_array)
            #Use the histogram classifier to predict if the contour is closest to tissue or artifact
            if np.argmax(probability_array) == 2:
                cnt_final.append(cnt)


    #Draw on the original image
    cv2.drawContours(image_down_2, cnt_final, -1, (0, 255, 255), 10)
    #plt.imshow(image_down_2)
    #plt.show()

    slide = openslide.open_slide(path_to_image)
    path_to_tissue = dest_path
    image_name = os.path.splitext(path_to_image)[0]
    path_to_folder = os.path.join(path_to_tissue,image_name)
    try:
        os.makedirs(path_to_folder)
    except:
        #"folder already exists"
        return
    #Run through contours and grab tiles at high res image
    resolution_number = int(resolution_defined - 1)
    #print(resolution_number)
    for item in cnt_final:
        resolution_calculated = 2**resolution_number
        factor = int(32/resolution_calculated)
        item = item * factor
        item = item[:,0,:]
        xx,yy = item.T
        min_x = min(xx)
        min_y = min(yy)
        max_x = max(xx)
        max_y = max(yy)

        x_iterator = int(min_x)
        y_iterator = int(min_y)
        counter = 0
        while x_iterator < max_x:
            y_iterator = int(min_y)
            while y_iterator < max_y:
                #print(x_iterator)
                #print(y_iterator)
                #print(type(x_iterator))
                #print(type(y_iterator))
                #print(slide.level_dimensions[resolution_number])
                image_crop = np.array(slide.read_region((x_iterator, y_iterator), resolution_number, (tile_size, tile_size)))
                image_crop = cv2.cvtColor(image_crop, cv2.COLOR_RGB2BGR)
                file_name = str(x_iterator) + "_" + str(y_iterator) + ".png"
                file_name_final = os.path.join(path_to_folder,file_name)
                image_mean = np.mean(np.mean(image_crop, axis=(0, 1)),axis = 0)
                #Make sure not all white or not all black
                if 10 < image_mean <240:
                    cv2.imwrite(file_name_final, image_crop)

                y_iterator += tile_size

            counter += 1
            # image_crop = mrxs_slide.read_region((x_iterator, y_iterator), 0, (x_iterator+256, y_iterator+256))
            #image_crop = np.array(mrxs_slide.read_region((x_iterator, y_iterator), -1, (256, 256)))

            #file_name = str(x_iterator) + "_" + str(y_iterator) + ".png"
            #if len(np.unique(image_crop)) > 1:
            #    cv2.imwrite(file_name, image_crop)
            x_iterator += tile_size

def worker(arg):
    obj = arg
    return find_contours(obj)

def multi_run_wrapper(args):
   return add(*args)
#Path to where images are
path_to_images = r"S:\\Official_Image_Server\\Studies\\Study\\"
#Path for tiles
destination_path = r"G:\Studies\Tissue_tiles_2"
#These are images that are examples of the artifacts you want to exclude
#artifact 1 and 2 are artifacts, the tissue is the tissue you are trying to find
#Can just be simple pngs that are bounding boxes of the tissue
artifact_1 = cv2.imread(r"C:\Users\Spare\Documents\Whatisthisfolder\1.PNG")
artifact_2 = cv2.imread(r"C:\Users\Spare\Documents\Whatisthisfolder\2.PNG")
tissue_1 = cv2.imread(r"C:\Users\Spare\Documents\Whatisthisfolder\3.PNG")

#Specify tile size here
tile_size_param = 256
#Resolution you want, only full res works right now...
res = 1

#Compile the classifier
my_classifier = HistogramColorClassifier(channels=[0, 1, 2],
                                         hist_size=[128, 128, 128],
                                         hist_range=[0, 256, 0, 256, 0, 256],
                                         hist_type='BGR')
my_classifier.addModelHistogram(artifact_1)
my_classifier.addModelHistogram(artifact_2)
my_classifier.addModelHistogram(tissue_1)

mrxs_list = []
dest_list = []
class_list = []
tile_size_list = []
resolution_list = []

if __name__ == '__main__':
    for item in os.listdir(path_to_images):
        os.chdir(path_to_images)
        if item.endswith(".mrxs"):
            mrxs_list.append(item)
            dest_list.append(destination_path)
            class_list.append(my_classifier)
            tile_size_list.append(tile_size_param)
            resolution_list.append(res)

    #freeze_support()

    pool = ThreadPool(1)

    list_of_results = pool.starmap(find_contours, zip(mrxs_list,dest_list,class_list,tile_size_list,resolution_list))
    pool.close()
    pool.join()


