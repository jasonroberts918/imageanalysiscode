import os
import openslide
import numpy as np
import cv2
import pandas as pd
import json
from scipy import ndimage


#PATH TO JSONS FROM QUPATH
path_to_txt = r""

#PATH TO MRXS FILES
path_to_img = r""

dict_out = {}


for item in os.listdir(path_to_txt):

    txt_path = open(os.path.join(path_to_txt,item))
    data_loaded = json.load(txt_path)
    #Change extension if its different
    image_name = os.path.basename(item).split('.')[0]  + ".mrxs"
    print(image_name)
    mrxs_load = openslide.open_slide(os.path.join(path_to_img,image_name))

    f = 0
    t = 0
    for i in (data_loaded):
        t+=1

        cell_coord = i['geometry']['coordinates'][0]
        classification = i['properties']['classification']['name']

        #Change to what you call potential ballooning cells
        if classification == "Negative":
            ctr = np.array(cell_coord).reshape((-1, 1, 2)).astype(np.int32)

            #This is a reasonable number, this is in pixels so it may change if its from a different scanner
            #Can move up/down depending on sample and species
            if cv2.contourArea(ctr) > 30000:
                coord_max = np.amax(ctr,axis=0)
                coord_min = np.amin(ctr,axis=0)
                x_max = coord_max[0][0]
                y_max = coord_max[0][1]
                x_min = coord_min[0][0]
                y_min = coord_min[0][1]
                x_dist = x_max - x_min
                y_dist = y_max - y_min
                region_loaded = np.array(mrxs_load.read_region((x_min,y_min),0,(x_dist,y_dist)))
                imgray = cv2.cvtColor(region_loaded, cv2.COLOR_BGR2GRAY)

                ret, thresh = cv2.threshold(imgray, 225, 255, 0)
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


                if len(contours) > 80:
                    print(t)
                    varianceMatrix = ndimage.generic_filter(imgray, np.var, size=3)
                    print((np.array(varianceMatrix).mean()))

                    #The 70 here is reasonable for a normal H&E, if its darker or lighter/more contrast you will have to change it
                    #The more contrast/darker, the higher the threshold and vice-versa
                    if (np.array(varianceMatrix).mean()) > 70:

                        #try:
                            #(x_1, y_1), (MA, ma), angle = cv2.fitEllipse(ctr)
                            #eccentricity_calc = MA / ma
                            #approx = cv2.approxPolyDP(ctr[i], 0.01 * cv2.arcLength(ctr[i], True), True)
                        #except:
                            #approx = 0
                            #eccentricity_calc = 0


                        #print(np.array(varianceMatrix).mean())


                        print(t)
                        print('added a count!')
                        f+=1
                        #cv2.imshow('image', region_loaded)
                        #cv2.waitKey(0)

    dict_out[image_name] = f
    print('final tally is: ' + str(f))

                        #print(len(contours))

                        #cv2.imshow('image', thresh)
                        #cv2.waitKey(0)


out_df = pd.DataFrame.from_dict(dict_out, orient='index')
out_df.to_excel("Ballooning_data.xlsx")