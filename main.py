import pyopencl as cl
import numpy as np
from time import time
import PIL

import FileManager
from FileManager import Scene
from KernelLauncher import KernelLauncher

def main(scene):
    # --------------------------#
    #          context
    # --------------------------#
    #Open CL Context
    # Create a compute context
    platform = cl.get_platforms()
    my_gpu_devices = platform[0].get_devices()
    context = cl.Context(devices=my_gpu_devices)
    # Create a command queue
    queue = cl.CommandQueue(context)
    #KernelLauncher
    Klauncher = KernelLauncher(context,platform,my_gpu_devices[0],queue)


    #time statistic
    startTime = time()

    # --------------------------#
    #         settings
    # --------------------------#
    imgResolution = 512
    spp = 1000

    #--------------------------------#
    #         host buffers
    #--------------------------------#
    # source img
    # | r | g | b | as floats
    inputImg = np.zeros(imgResolution*imgResolution*3).astype(np.float32)

    for i in range(imgResolution):
        for j in range(imgResolution):
            for c in range(3):
                inputImg[i*3 + j*imgResolution*3 + c] = (1/imgResolution)*i

    # output img
    outImg = np.zeros(imgResolution*imgResolution*3).astype(np.float32)

    #camera
    #|position|direction|resX|resY| size|FOV|
    #|x  x   x|x   x   x|  x |  x | x   | x |
    cam = np.array([0,-3.5,0,
                    1,0,0,
                    imgResolution,imgResolution,1,3.14/4.0]).astype(np.float32)

    #--------------------------------#
    #          Computation
    #--------------------------------#
    print("#-----------------------------------------------------#")
    print("#-----------------------#")
    print("#    Start rendering    #")
    print("#-----------------------#")

    #arg: h_img_out, h_vertex_p,h_vertex_n,h_vertex_uv, h_face_data, h_material_data, h_cam, imgDim, spp
    Klauncher.launch_Raytracing(outImg,scene.V_p,scene.V_n,scene.V_uv,scene.faceData,scene.materialData,cam,imgResolution*imgResolution,spp)


    inputImg = outImg
    print("==> Done")

    #--------------------------------#
    #          Image output
    #--------------------------------#
    print("#-----------------------#")
    print("#    image export       #")
    print("#-----------------------#")
    #Klauncher.launch_ImgProcessing(inputImg,outImg,imgResolution)
    print("Gamma correction ==> DONE")

    # save img to disk
    FileManager.saveImg(outImg.reshape((imgResolution, imgResolution, 3)), imgResolution, imgResolution, "output/out")
    FileManager.saveImg(inputImg.reshape((imgResolution, imgResolution, 3)), imgResolution, imgResolution, "output/src")
    print("Image saved to disk ==> DONE \n")

    execTime = time()-startTime
    print("#--------------------------#")
    print("#           DONE           #")
    print("#--------------------------#\n")
    print("Executed in : " + "{:10.0f}".format(execTime) + "sec\n")
