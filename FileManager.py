import sys
import fileinput
import os.path
from os import path
from numpy import random
import pywavefront
import numpy as np
from PIL import Image
from BVH import *
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d.art3d import Line3DCollection

#----------------------------------
#   SCENE IMPORTER
#----------------------------------
# create vertexData and materialData arrays
# directly usable by the raytracing Kernel
# stored in a scene object
#----------------------------------
class Scene(object):

    def plot_linear_cube(self,ax, min,max, color='red', alpha = 0.5):
        x=min[0]
        y=min[1]
        z=min[2]

        dx = max[0]-x
        dy = max[1]-y
        dz = max[2]-z

        xx = [x, x, x+dx, x+dx, x]
        yy = [y, y+dy, y+dy, y, y]
        kwargs = {'alpha': alpha, 'color': color}
        ax.plot3D(xx, yy, [z]*5, **kwargs)
        ax.plot3D(xx, yy, [z+dz]*5, **kwargs)
        ax.plot3D([x, x], [y, y], [z, z+dz], **kwargs)
        ax.plot3D([x, x], [y+dy, y+dy], [z, z+dz], **kwargs)
        ax.plot3D([x+dx, x+dx], [y+dy, y+dy], [z, z+dz], **kwargs)
        ax.plot3D([x+dx, x+dx], [y, y], [z, z+dz], **kwargs)

    def plotTri(self,ax,id):
        x = [self.V_p[3*int(self.faceData[10*id + 7])+0], self.V_p[3*int(self.faceData[10*id + 8])+0], self.V_p[3*int(self.faceData[10*id + 9])+0]]
        y = [self.V_p[3*int(self.faceData[10*id + 7])+1], self.V_p[3*int(self.faceData[10*id + 8])+1], self.V_p[3*int(self.faceData[10*id + 9])+1]]
        z = [self.V_p[3*int(self.faceData[10*id + 7])+2], self.V_p[3*int(self.faceData[10*id + 8])+2], self.V_p[3*int(self.faceData[10*id + 9])+2]]
        verts = [list(zip(x,y,z))]
        
        ax.add_collection3d(Poly3DCollection(verts,facecolors=(random.uniform(),random.uniform(),random.uniform()),zsort='min', linewidths=1))
        ax.add_collection3d(Line3DCollection(verts, colors='k', linewidths=1))

    def intersectBox(self,ro, rdir, b):
        
        tmin = (b.min[0] - ro[0]) / rdir[0]
        tmax = (b.max[0] - ro[0]) / rdir[0]
    
        if (tmin > tmax):
            t = tmin
            tmin = tmax
            tmax = t
        
        tymin = (b.min[1] - ro[1]) / rdir[1]
        tymax = (b.max[1] - ro[1]) / rdir[1]
    
        if (tymin > tymax):
            ty = tymin
            tymin = tymax
            tymax = ty
    
        if ((tmin > tymax) or (tymin > tmax)):
            return False
    
        if (tymin > tmin):
            tmin = tymin 
    
        if (tymax < tmax):
            tmax = tymax
    
        tzmin = (b.min[2] - ro[2]) / rdir[2]
        tzmax = (b.max[2] - ro[2]) / rdir[2] 
    
        if (tzmin > tzmax):  
            tz = tzmin
            tzmin = tzmax
            tzmax = tz
        if ((tmin > tzmax) or (tzmin > tmax)):
            return False
    
        if (tzmin > tmin):
            tmin = tzmin
    
        if (tzmax < tmax):
            tmax = tzmax
    
        return True


    def interNode(self,ro,rdir, curr):

        min = [self.BVH.exportArray[9*curr + 2],self.BVH.exportArray[9*curr + 3],self.BVH.exportArray[9*curr + 4]]
        max = [self.BVH.exportArray[9*curr + 5],self.BVH.exportArray[9*curr + 6],self.BVH.exportArray[9*curr +7]]
        b = Box(min,max)
        
        return self.intersectBox(ro,rdir,b)
    

    def testRay(self,ro,rdir, n, result):
        if (self.intersectBox(ro,rdir,n.box) or 0):
            if (len(n.array) == 0): #interior node
                self.testRay(ro,rdir, self.BVH.nodeList[n.childL], result)
                self.testRay(ro,rdir, self.BVH.nodeList[n.childR], result)
            
            else:
                result.append(n.array[0][10])
        return
    


    def test(self):
        curr = 0
        S=[]
        T=[]
        n=0

        S.append(0)
        fig = plt.figure()
        ax = Axes3D(fig)
    
        ro = [-0.5,-0.5,-0.5]
        rdir = [0.001,1,0.001]
        kwargs = {'alpha': 1, 'color': 'k'}
        ax.plot3D([ro[0], ro[0]+rdir[0]], [ro[1], ro[1]+rdir[1]], [ro[2], ro[2]+rdir[2]], **kwargs)

        """ result = []
        self.testRay(ro,rdir,self.BVH.root,result)
        print(result)
        print(len(result))

        for i in range(0,len(result)):
            #print(result[i])
            self.plotTri(ax,result[i])

        curr = 0
        Bmin = [self.BVH.exportArray[int(9*curr+2)],self.BVH.exportArray[int(9*curr+3)],self.BVH.exportArray[int(9*curr+4)]]
        Bmax = [self.BVH.exportArray[int(9*curr+5)],self.BVH.exportArray[int(9*curr+6)],self.BVH.exportArray[int(9*curr+7)]]
        self.plot_linear_cube(ax,Bmin,Bmax,color=(0,0,1),alpha=10/36) """

        while len(S)!=0:
            curr = S.pop()

            if(self.interNode(ro,rdir,int(curr)) or 0):
                if(self.BVH.exportArray[int(9*curr+8)] != -1):
                    print("node = "+str(curr)+ " |tri = " + str(self.BVH.exportArray[int(9*curr+8)]))
                    Bmin = [self.BVH.exportArray[int(9*curr+2)],self.BVH.exportArray[int(9*curr+3)],self.BVH.exportArray[int(9*curr+4)]]
                    Bmax = [self.BVH.exportArray[int(9*curr+5)],self.BVH.exportArray[int(9*curr+6)],self.BVH.exportArray[int(9*curr+7)]]
                    
                    self.plotTri(ax,int(self.BVH.exportArray[int(9*curr+8)]))
                    self.plot_linear_cube(ax,Bmin,Bmax,color=(1,0,0),alpha=20/36)
                    n=n+1


                if (self.BVH.exportArray[int(9*curr)] != -1):
                    S.append(self.BVH.exportArray[int(9*curr)])
                if (self.BVH.exportArray[int(9*curr+1)] != -1):
                    S.append(self.BVH.exportArray[int(9*curr+1)])

        """ while len(S)!=0:
            curr = S.pop()
            if(self.BVH.exportArray[int(9*curr+8)] != -1):
                print("node = "+str(curr)+ " |tri = " + str(self.BVH.exportArray[int(9*curr+8)]))
                Bmin = [self.BVH.exportArray[int(9*curr+2)],self.BVH.exportArray[int(9*curr+3)],self.BVH.exportArray[int(9*curr+4)]]
                Bmax = [self.BVH.exportArray[int(9*curr+5)],self.BVH.exportArray[int(9*curr+6)],self.BVH.exportArray[int(9*curr+7)]]
                self.plotTri(ax,int(self.BVH.exportArray[int(9*curr+8)]))
                self.plot_linear_cube(ax,Bmin,Bmax,color=(1,0,0),alpha=20/36)
                #
            n=n+1

            Bmin = [self.BVH.exportArray[int(9*curr+2)],self.BVH.exportArray[int(9*curr+3)],self.BVH.exportArray[int(9*curr+4)]]
            Bmax = [self.BVH.exportArray[int(9*curr+5)],self.BVH.exportArray[int(9*curr+6)],self.BVH.exportArray[int(9*curr+7)]]
            if(curr==5):
                self.plot_linear_cube(ax,Bmin,Bmax,color=(0,1,0),alpha=1)
            else:
                self.plot_linear_cube(ax,Bmin,Bmax,color=(0,0,1),alpha=10/36)
            if (self.BVH.exportArray[int(9*curr)] != -1):
                if(self.interNode(ro,rdir,int(curr))):
                    S.append(self.BVH.exportArray[int(9*curr)])
            if (self.BVH.exportArray[int(9*curr+1)] != -1):
                if(self.interNode(ro,rdir,int(curr))):
                    S.append(self.BVH.exportArray[int(9*curr+1)]) """

        print("n=" + str(n))


        
        plt.title('BVH')
        plt.show()
        print("done")





        

       
        
        


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
        self.V_p = np.reshape(self.V_p,(1,len(self.V_p)*3))[0]

        self.V_n = np.array(s.parser.normals).astype(np.float32)
        self.V_n = np.reshape(self.V_n,(1,len(self.V_n)*3))[0]

        self.V_uv = np.array(s.parser.tex_coords).astype(np.float32)
        self.V_uv = np.reshape(self.V_uv,(1,len(self.V_uv)*2))[0]

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
        self.V_p = []
        self.V_n = []
        self.V_uv = []
        #|mat|UVindex|Normal index|position index|
        #| x |x  x  x|x    x     x|x      x     x|
        self.faceData = []
        self.faceData_ChunkSize = 10
        # type | color | Roughness | ior |
        # 1    | 1 1 1 | 1         | 1  
        self.materialData = []
        self.materialData_ChunkSize = 6

        self.materialCount = 0
        self.materialLength = []

        self.path = path
        self.importSceneGeometry(path)
        self.config = configReader(path.replace(".obj",".ini"),self.materialCount)
        self.importMaterialData()
        self.BVH = BVH(self.faceData,self.V_p)

        #self.test()

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