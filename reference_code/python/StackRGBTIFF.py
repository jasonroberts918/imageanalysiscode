'''

Inception project
Combine single channel fluorescence tiff images
Output a pyramidal jpg that can be opened by QuPath for cell segmentation
Channel order is RGB or Cy5-TRITC-DAPI
So for QuPath need to use channels 1 and 2 for cells to get the intensity numbers out
different paths inserted here for new set of samples

Q value in the end could perhaps be adjusted to reduce final file size

'''


import os.path
import pyvips
import time
import cv2
import numpy as np
from PIL import Image


#np.set_printoptions(threshold=np.nan)
#Image.MAX_IMAGE_PIXELS = 9933120000
def vips2numpy(vi):
    return np.ndarray(buffer=vi.write_to_memory(),
                      dtype=format_to_dtype[vi.format],
                      shape=[vi.height, vi.width, vi.bands])

def numpy2vips(a):
    height, width, bands = a.shape
    linear = a.reshape(width * height * bands)
    vi = pyvips.Image.new_from_memory(linear.data, width, height, bands,
                                      dtype_to_format[str(a.dtype)])
    return vi

format_to_dtype = {
    'uchar': np.uint8,
    'char': np.int8,
    'ushort': np.uint16,
    'short': np.int16,
    'uint': np.uint32,
    'int': np.int32,
    'float': np.float32,
    'double': np.float64,
    'complex': np.complex64,
    'dpcomplex': np.complex128,
}

dtype_to_format = {
    'uint8': 'uchar',
    'int8': 'char',
    'uint16': 'ushort',
    'int16': 'short',
    'uint32': 'uint',
    'int32': 'int',
    'float32': 'float',
    'float64': 'double',
    'complex64': 'complex',
    'complex128': 'dpcomplex',
}

#Do note that all of the .tif files to process need to have some certain formatting names about them
#Because that's how we search for them... so later in there's a loop that looks for file.lower "dapi"
#If all your files are called something else, then you may want to change what the program looks for


#Path where your tiff files and subdirectories are
path = r"K:\20-318 Kallyope\TIFF Stacks"

os.chdir(path)

folders = os.listdir(path)

# get only the relevant folders
ls = []
for fol in folders:
    #VERY IMPORTANT LINE
    #Make sure that the string matches some common name in ALL YOUR FILES like the study ID or the name
    #you can always double check by cross referencing the number of files to process vs the number actually in there
    #if 'Vical' in fol:
    ls.append(fol)
folders = ls
print(len(ls))
#A Path for all your final .tif files to go, doesn't really matter where it is, just that it's there
path_pyramids = r"K:\20-318 Kallyope\DFC"
pyramids = os.listdir(path_pyramids)
pyramids = [x.split('_Wholeslide')[0] for x in pyramids]
folders_left = []
for fol in folders:
    if fol not in pyramids:
        folders_left.append(fol)


# now work with folders left
j = 0

total_files = len(folders_left)
print('total files to process', total_files)

for i in range(len(folders_left)):
    StartTime = time.clock()

    print('files left', total_files - i)

    fold1 = folders_left[i]
    fold1_path = os.path.join(path, fold1)

    os.chdir(fold1_path)
    files1 = os.listdir(fold1_path)

    # get correct files based on channel names

    for f in files1:

        print('Current Folder is:' + str(f))
        try:
            if 'dapi' in f.lower():
                file_b = f
                print("found a blue fun")

            if 'fitc' in f.lower():
                file_g = f
                print("found a green fun")
            if 'cy5-quad' in f.lower():
                file_r = f
                print("found a red fun")

        except:
            continue

    try:
        img_b = pyvips.Image.new_from_file(file_b)
        print(img_b)
        print("hello")
        ar = np.zeros(dtype=format_to_dtype[img_b.format],
                      shape=[img_b.height, img_b.width, 1])
        height, width, bands = ar.shape

        linear = ar.reshape(width * height * bands)

        vi = pyvips.Image.new_from_memory(linear.data, width, height, bands,
                                          dtype_to_format[str(ar.dtype)])

        #bb.tiffsave("lol.tif",compression='jpeg',Q=92,tile=True,pyramid=True,xres=322.5,yres=332.5,background=0)


    except:
        img_b = pyvips.Image.new_from_file(file_b)
        #print("Blue image is: " + img_b)

        print('didnt open dapi')
        j += 1
        print('files failed so far', j)
        continue

    # make an empty pyvips array



    try:
        print("Found FITC")
        img_g = pyvips.Image.new_from_file(file_g)
        print(img_g)
    except:
        print("Except G")
        img_g = vi

    try:
        img_r = pyvips.Image.new_from_file(file_r)
        print(img_r)
    except:
        print("Except R")
        img_r = vi
    lol = pyvips.Image.bandjoin(img_r, img_g )
    lol = pyvips.Image.bandjoin(lol,img_b )
    print(lol)
    #img_ch = pyvips.Image.bandjoin(img_r, img_g)
    #img_ch = pyvips.Image.bandjoin(img_ch, img_b)

    fname = file_b.split('.tif')[0] + '_pyramid_.tiff'
    f_path = os.path.join(path_pyramids, fname)

    lol.tiffsave(f_path,
                  compression = 'jpeg',
                  Q = 92,
                  tile = True,
                  pyramid = True,
                  xres = 322.5,
                  background = 0,
                  yres = 332.5
                  )
    endtime = time.time()
print('total files failed', j)
