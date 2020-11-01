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
    # mat | vertex | normal | textureCoord |
    # 1   | 1  1  1| 1 1 1  | 1 1
    vertexData = []
    vertexData_ChunkSize = 8
    # type | color | Roughness | ior |
    # 1    | 1 1 1 | 1         | 1  
    materialData = []
    materialData_ChunkSize = 6

    materialCount = 0

    def __init__(self,path):

        print("#-----------------------#")
        print("#    import object      #")
        print("#-----------------------#")

        matSavedFilePath = path.split(".")[0]

        s = pywavefront.Wavefront(path,collect_faces=True,create_materials=True)
        mat = s.materials

        print("import vertex data :")
        self.vertexData = []
        self.materialCount = 0
        for name, material in mat.items():
            print("import material vertex '" + name + "'")
            #vertexData building
            #insert 'matCount' every 'rank' values
            i = 0
            while i < len(material.vertices):
                material.vertices.insert(i, self.materialCount)
                i += (self.vertexData_ChunkSize+1)
            self.materialCount+=1
            self.vertexData = self.vertexData + material.vertices

        print("==> DONE")
        print("import material data")

        #load from file, create new file if it doesn't exist
        try:
            self.materialData = np.load(matSavedFilePath+".npy")
        except IOError as error:
            print(error)
            print("creating new material save file")
            self.materialData = np.zeros((1,self.materialData_ChunkSize*self.materialCount))
            np.save("ObjFiles/Cornell box",self.materialData)

        print("==> DONE\n")

#export array[SizeX*SizeY*3] (float) into .png file
def saveImg(data,sizeX,sizeY,name):
    #gammaCorrection(data,N,N)
    img = Image.fromarray((data*255).astype('uint8'),"RGB")
    img.save(name + ".png")
    return



