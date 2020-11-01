import pyopencl as cl
import numpy as np
from time import time
import PIL

import FileManager
from FileManager import Scene
from KernelLauncher import KernelLauncher

# --------------------------#
#          context
# --------------------------#
#Open CL Context
# Create a compute context
platform = cl.get_platforms()[0]
device = platform.get_devices()[0]
context = cl.Context([device])
# Create a command queue
queue = cl.CommandQueue(context)
#KernelLauncher
Klauncher = KernelLauncher(context,platform,device,queue)

#scene import
scene = Scene("ObjFiles/Cornell box.obj")

#time statistic
startTime = time()

# --------------------------#
#         settings
# --------------------------#
imgResolution = 1024

#--------------------------------#
#         host buffers
#--------------------------------#
# source img
inputImg = np.zeros(imgResolution*imgResolution*3).astype(np.float32)

for i in range(imgResolution):
    for j in range(imgResolution):
        for c in range(3):
            inputImg[i*3 + j*imgResolution*3 + c] = (1/imgResolution)*i

# output img
outImg = np.zeros(imgResolution*imgResolution*3).astype(np.float32)

#--------------------------------#
#          Image output
#--------------------------------#
print("#-----------------------#")
print("#    image export       #")
print("#-----------------------#")
Klauncher.launch_ImgProcessing(inputImg,outImg,imgResolution)
print("Gamma correction ==> DONE")

# save img to disk
FileManager.saveImg(outImg.reshape((imgResolution, imgResolution, 3)), imgResolution, imgResolution, "output/test")
FileManager.saveImg(inputImg.reshape((imgResolution, imgResolution, 3)), imgResolution, imgResolution, "output/src")
print("Image saved to disk ==> DONE \n")

execTime = time()-startTime
print("#--------------------------#")
print("#           DONE           #")
print("#--------------------------#\n")
print("Executed in : " + "{:10.0f}".format(execTime) + "sec\n")
