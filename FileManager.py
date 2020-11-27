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

    def getMaterialInfo(self,matId,argId):
        offset = matId*self.materialData_ChunkSize
        if(argId == 0): #return type
            return self.materialData[offset+0].astype(float)
        if(argId == 1): #return color
            return tuple(self.materialData[offset+1 : offset+4])
        else: #return roughness or ior
            return self.materialData[offset+argId+2].astype(float)

    def setMaterialInfo(self,matId,argId,newValue):
        offset = matId*self.materialData_ChunkSize
        if(argId == 0): #set type
            self.materialData[offset+0] = newValue
            self.updateMatData()
            return
        if(argId == 1): #set color
            self.materialData[offset+1] = min(newValue[0],1.0)
            self.materialData[offset+2] = min(newValue[1],1.0)
            self.materialData[offset+3] = min(newValue[2],1.0)
            self.updateMatData()
            return
        else: #set roughness or ior
            self.materialData[offset+argId+2] = newValue
            self.updateMatData()
            return

    def updateMatData(self):
            print("saving Material to disk")
            np.save("ObjFiles/Cornell box",self.materialData.astype(np.float32))

    def __init__(self,path):

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
        print("import material data")

        #load from file, create new file if it doesn't exist
        try:
            self.materialData = np.load(matSavedFilePath+".npy").astype(np.float32)
        except IOError as error:
            print(error)
            print("creating new material save file")
            self.materialData = np.zeros(self.materialData_ChunkSize*(self.materialCount+1)).astype(np.int32)
            np.save("ObjFiles/Cornell box",self.materialData)

        print("import vertex data :")
        self.V_p = np.array(s.vertices).astype(np.float32)
        self.V_p = np.reshape(self.V_p,(1,len(self.V_p)*3))

        self.V_n = np.array(s.parser.normals).astype(np.float32)
        self.V_n = np.reshape(self.V_n,(1,len(self.V_n)*3))

        self.V_uv = np.array(s.parser.tex_coords).astype(np.float32)
        self.V_uv = np.reshape(self.V_uv,(1,len(self.V_uv)*2))

        self.materialData = np.array(self.materialData).astype(np.float32)
        self.faceData = np.array(self.faceData).astype(np.int32)
        print("==> DONE\n")

#export array[SizeX*SizeY*3] (float) into .png file
def saveImg(data,sizeX,sizeY,name):
    #gammaCorrection(data,N,N)
    img = Image.fromarray((data*255).astype('uint8'),"RGB")
    img.save(name + ".png")
    return