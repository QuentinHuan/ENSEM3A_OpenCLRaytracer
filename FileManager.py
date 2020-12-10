import sys
import fileinput
import os.path
from os import path
import pywavefront
import numpy as np
from PIL import Image

#----------------------------------
#   SCENE IMPORTER
#----------------------------------
# create vertexData and materialData arrays
# directly usable by the raytracing Kernel
# stored in a scene object
#----------------------------------
class Scene(object):
    V_p = []
    V_n = []
    V_uv = []
    #|mat|UVindex|Normal index|position index|
    #| x |x  x  x|x    x     x|x      x     x|
    faceData = []
    faceData_ChunkSize = 10
    # type | color | Roughness | ior |
    # 1    | 1 1 1 | 1         | 1  
    materialData = []
    materialData_ChunkSize = 6


    materialCount = 0
    materialLength = []

    def importSceneGeometry(self,path):
        print("#-----------------------#")
        print("#    import object      #")
        print("#-----------------------#")

        matSavedFilePath = path.split(".")[0]

        s = pywavefront.Wavefront(path,collect_faces=False,create_materials=True)
        mat = s.materials

        print("import face data :")

        try:
            f = open(path)
            matCounter = 0
            line = f.readline()
            while line.split(" ")[0] != "usemtl":
                line = f.readline()
            print("faceContent")
            if(line.split(" ")[0] == "usemtl"):
                while line:
                    line = f.readline()
                    if(not line): break
                    if line[0] == "f":
                        self.faceData.append(matCounter)
                        splitSpace = line.split(" ")
                        for i in (1,2,0):#each component
                            for j in range(1,4):#each 3 vertex
                                splitSlash = splitSpace[j].split("/")
                                self.faceData.append(int(splitSlash[i])-1)
                    else:
                        if line[0] == "u":
                            matCounter = matCounter + 1
                    
            f.close()
        except IOError:
            print(".obj file not found.")

        self.materialCount = matCounter
        print("==> DONE")
        
        print("import vertex data :")
        self.V_p = np.array(s.vertices).astype(np.float32)
        self.V_p = np.reshape(self.V_p,(1,len(self.V_p)*3))

        self.V_n = np.array(s.parser.normals).astype(np.float32)
        self.V_n = np.reshape(self.V_n,(1,len(self.V_n)*3))

        self.V_uv = np.array(s.parser.tex_coords).astype(np.float32)
        self.V_uv = np.reshape(self.V_uv,(1,len(self.V_uv)*2))

        self.faceData = np.array(self.faceData).astype(np.int32)
        print("==> DONE\n")

    def importMaterialData(self):
        print("import material data")
        self.materialData = []
        param = self.config.loadParameters()

        materialKeys = []
        for k in param.keys():
            if(k.split("_")[0] == "M"):
                materialKeys.append(k)

        for k in materialKeys:
            self.materialData.append(param[k])


        self.materialData = np.array(self.materialData).astype(np.float32)
        print("==> DONE\n")

    #path is the .obj file path
    def __init__(self,path):
        self.path = path
        self.importSceneGeometry(path)
        self.config = configReader(path.replace(".obj",".ini"),self.materialCount)
        self.importMaterialData()

    def loadParameters(self):
        return self.config.loadParameters()

       

#export array[SizeX*SizeY*3] (float) into .png file
def saveImg(data,sizeX,sizeY,name):
    #gammaCorrection(data,N,N)
    img = Image.fromarray((data*255).astype('uint8'),"RGB")
    img.save(name + ".png")
    return


#----------------------------------
#     SCENE PARAMETER READER
#----------------------------------
# read the scene config file at path
# the config file is used to keep track of:
#    -camera position
#    -material values
#    -render parameters
#----------------------------------
class configReader(object):

    def __init__(self,scenepath, materialCount):
        self.configPath = scenepath

        #default fill if file doesn't exist
        if(not path.exists(scenepath)):
            f = open(scenepath, "w")
            f.write("sceneFile=" + scenepath+"\n"+
"""resolution=256
spp=10
maxBounce=4
""")
            f.close()
            for i in range(materialCount+1):
                self.setParameter("M_"+str(i)+"_Type",1)
                self.setParameter("M_"+str(i)+"_Color_R",1)
                self.setParameter("M_"+str(i)+"_Color_G",1)
                self.setParameter("M_"+str(i)+"_Color_B",1)
                self.setParameter("M_"+str(i)+"_roughness",0)
                self.setParameter("M_"+str(i)+"_ior",0)

    def getParameter(self,param):
        configFile = open(self.configPath,mode="r")
        Lines = configFile.readlines() 
    
        # Strips the newline character 
        for line in Lines: 
            split = line.split('=')
            if(split[0] == param):
                configFile.close()
                return split[1].split("\n")[0] 
        configFile.close()
        return ""

    #return a dictionary filled with the parameters
    def loadParameters(self):
        parameters = {}
        configFile = open(self.configPath,mode="r")
        Lines = configFile.readlines() 
    
        for line in Lines: 
            split = line.split('=')
            parameters[split[0]] = split[1].split("\n")[0]
        configFile.close()
        return parameters

    def setParameter(self, param, value):
        found = False
        for line in fileinput.input([self.configPath], inplace=True):
            if line.strip().startswith(param+"="):
                line = param+"="+ str(value)+"\n"
                found = True
            sys.stdout.write(line)

        if(not found):
            line = param+"="+ str(value)+"\n"
            file = open(self.configPath,mode="a")
            file.write(line)
            file.close

        print("set parameter '"+param+"' to " + str(value))