import numpy as np
from numpy.core.defchararray import array



class Box(object):
    def __init__(self,min,max):
        self.min = min
        self.max = max
        #self.center = (min+max)/2


class Node(object):

    #interior node
    #array is an array of faceData
    def __init__(self, array, V_p):
        self.array = array
        self.V_p = V_p
        self.box = self.computeBoundingBox()
        self.childL = -1
        self.childR = -1

    #configure children
    def addChild(self,childL,childR):
        self.childR = childR
        self.childL = childL
        self.array = []

    #return triangle center
    def computeTriCenter(self,triangle):
        a = np.zeros((3,1))
        b = np.zeros((3,1))
        c = np.zeros((3,1))

        for x in range(0,3):
            a[x]= self.V_p[3*triangle[7]+x]
            b[x]= self.V_p[3*triangle[8]+x]
            c[x]= self.V_p[3*triangle[9]+x]

        return (a+b+c)/3

    def computeBoundingBox(self):
        epsilon = 0
        X = []
        Y = []
        Z = []
        vMin = np.zeros((3,1))
        vMax = np.zeros((3,1))
        if len(self.array) == 0:
            return Box(vMin,vMax)
        else:
            #each triangle
            for t in self.array:
                #each vertex
                for id in range(7,10):
                    X.append(self.V_p[3*t[id]+0])
                    Y.append(self.V_p[3*t[id]+1])
                    Z.append(self.V_p[3*t[id]+2])

            vMin[0] = np.min(X)-epsilon
            vMin[1] = np.min(Y)-epsilon
            vMin[2] = np.min(Z)-epsilon

            vMax[0] = np.max(X)+epsilon
            vMax[1] = np.max(Y)+epsilon
            vMax[2] = np.max(Z)+epsilon

            return Box(vMin,vMax)

    #split a Node in two
    def split(self,BVH):
        #split interrior node
        if(len(self.array)>1):
            #---------------------
            #split method
            #---------------------
            var = np.zeros((3,1))
            mean = np.zeros((3,1))
            #compute mean
            c = 0
            self.L = []

            for t in self.array:
                self.L.append(self.computeTriCenter(t))

            """ for v in L:
                mean = mean + v
            mean = mean / len(L) """
            mean = np.mean(self.L,axis=0)

            """ #compute variance
            for v in L:
                var = var + (v-mean)**2
            var = var / len(L) """
            var = np.var(self.L,axis=0)

            #split onlong the maximum variance axis, on the mean centroid value
            #find the split axis
            splitAxis = np.argmax(var) # 0->x | 1->y | 2->z
            #on point
            splitPivot = mean[splitAxis]

            #---------------------
            #       split
            #---------------------

            #split along the axis
            arrayR = []
            arrayL = []

            for i in range(len(self.L)):
                if self.L[i][splitAxis] < splitPivot:
                    arrayL.append(self.array[i])
                else:
                    arrayR.append(self.array[i])
            BVH.addNode(Node(arrayL,self.V_p))
            BVH.addNode(Node(arrayR,self.V_p))
            self.addChild(BVH.NodeCounter-2,BVH.NodeCounter-1)

            #erase the now empty interrior node
            self.array = []
            return
        #leaf creation
        else:
            self.computeBoundingBox()
            return

class BVH(object):

    #interior node
    #
    def __init__(self, faceData, V_p):
        self.V_p = V_p
        self.triangleList = []
        self.exportArray = []
        self.counter = -1
        self.NodeCounter = 0
        self.nodeList = []
        self.tempL = []
        
        for i in range(0,int(len(faceData)/10)):
            t = []
            for j in range(0,10):
                t.append(faceData[10*i + j])
            t.append(i)#add triangle ID
            self.triangleList.append(t)

        self.root = Node(self.triangleList,self.V_p)
        self.addNode(self.root)
        self.build(self.root)
        self.exportToKernelFormat()

    #build the BVH tree recursively
    def build(self,node):
        if (len(node.array) > 1): #interior node, split
            node.split(self)

            self.build(self.nodeList[node.childL])
            self.build(self.nodeList[node.childR])
            return
        
        else: #leaf node, stop here
            node.box = node.computeBoundingBox()
            return

    #write the tree as an array usable by the OpenCl kernel
    def exportToKernelFormat(self):
        self.recursiveRead()
        self.exportArray = np.array(self.exportArray).astype(np.float32)
        self.exportArray = np.reshape(self.exportArray,(1,len(self.exportArray)*9))[0]
        print("heoo")

    def add(self):
        self.counter = self.counter + 1

    def addNode(self,node):
        self.nodeList.append(node)
        self.NodeCounter = self.NodeCounter + 1
        


    def recursiveRead(self):
        for i in range(0,len(self.nodeList)):
            L = []
            L.append(self.nodeList[i].childL)
            L.append(self.nodeList[i].childR)
            for j in range(0,3):
                L.append(self.nodeList[i].box.min[j][0])
            for k in range(0,3):
                L.append(self.nodeList[i].box.max[k][0])


            T = self.nodeList[i].array
            if(len(self.nodeList[i].array) == 0):
                L.append(-1)
            else:
                L.append(self.nodeList[i].array[0][10])

            self.exportArray.append(L)







