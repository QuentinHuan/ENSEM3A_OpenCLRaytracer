import sys
from tkinter import *
from tkinter import ttk
from tkinter import colorchooser
from tkinter.filedialog import askopenfile 
from PIL import Image, ImageTk
from main import *
import numpy as np
from FileManager import Scene
from functools import partial

#-----------------------------
#           Utilities
#-----------------------------

#stdout redirector
class RedirectText(object):

    def __init__(self, text_ctrl):
        """Constructor"""
        self.output = text_ctrl
        
    def write(self, string):
        """"""
        self.output.insert(END, string)
        self.output.see(END)

    def flush(self):
        pass

def clamp(x): 
    return max(0, min(x, 255))

def toHex(colorToConvert):
    if(len(colorToConvert) == 3):
        r = int(colorToConvert[0]*255)
        g = int(colorToConvert[1]*255)
        b = int(colorToConvert[2]*255)
        return "#{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))




#-----------------------------
#      Button callbacks
#-----------------------------

#get the path the .obj file to render, store it in 'sceneFilePath'
#save the path in the file 'config.ini' for next time
def openObjFile(*args):
    global scene
    file = askopenfile(mode ='r', filetypes =[('Obj files', '*.obj')]) 
    if file is not None: 
        content = file.read() 
        sceneFilePath.set(file.name)
        file.close()
        configFile = open("config.ini",mode='w')
        configFile.write("sceneFile=" + sceneFilePath.get())
        configFile.close()
        scene = Scene(sceneFilePath.get())
        return content
    else:
        print("no .obj file")
        return NONE

#render the scene at 'sceneFilePath' using the main script
def render(*args):
    global RenderImage_Label
    path = sceneFilePath.get().split("/")
    sceneName = path[len(path)-1]
    print("ask to renderer scene '" + sceneName + "'")

    main(scene)
    load = Image.open("output/out.png")
    outputImg = ImageTk.PhotoImage(load)
    RenderImage_Label.configure(image=outputImg)
    RenderImage_Label.image = outputImg

def colorPicker(previousColor,matId):
    global pickedColor
    global MatButtons
    pickedColor = colorchooser.askcolor(MatButtons[matId].cget('bg'))
    out = [0,0,0]
    for i in range(3):
        out[i] = min(pickedColor[0][i]/255.0,1.0)
    print("pickedColor =" + str(out) + "HEX = " + pickedColor[1])
    scene.setMaterialInfo(matId,1,out)
    MatButtons[matId].configure(background = pickedColor[1])
    
def updateMatType(matId):
    global MatTypeSelectors
    global MatTypeLabel
    global matType
    print("updateMatType")
    scene.setMaterialInfo(matId,0,int(MatTypeSelectors[matId].get()))
    MatTypeLabel[matId].configure(text= matType[int(MatTypeSelectors[matId].get())])

#-----------------------------
#           Init
#-----------------------------
root = Tk()
root.tk.call('lappend', 'auto_path', 'awthemes-9.5.0')
root.tk.call('package', 'require', 'awdark')
ttk.Style().theme_use('awdark')
root.title("OpenCL Raytracer")

#load previous .obj scene file
sceneFilePath = StringVar()
configFile = open("config.ini",mode="r")
sceneFilePath.set(configFile.readline().split("=")[1])
configFile.close()

scene = Scene(sceneFilePath.get())

pickedColor = (0,0,0)

matType = {0 : "emissive",1 : "Diffuse",2 : "Glossy",3 : "Glass"}

#-----------------------------
#Layout Setup
#-----------------------------
#main frame
mainframe = ttk.Frame(root, padding="5 5 5 5")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

#divide top and bot
Top_frame = ttk.Frame(mainframe,padding="5 5 5 5")
Bot_frame = ttk.Labelframe(mainframe,padding="5 5 5 5",text='Console')
Top_frame.pack(side="top",fill='both',padx=5)
Bot_frame.pack(side="bottom",fill='both',padx=5)

#Left and Right Frame x | x
left_Top_frame = ttk.Frame(Top_frame,padding="5 5 5 5")
left_Top_frame.pack(side="left",fill='both',padx=5)
right_frame = ttk.Labelframe(Top_frame,text="Output Image")
right_frame.pack(side="right",fill='both',padx=5)

#-----------------------------
#Left Top Side
#-----------------------------

tabPannel = ttk.Notebook(left_Top_frame)
SceneTab = ttk.Frame(tabPannel)
#Material Tab
MatTab = ttk.Frame(tabPannel)

try:
    MaterialData = scene.materialData
    MatTypeLabel = []
    MatColorString = []
    MatButtons = []
    MatTypeSelectors = []
    for i in range(scene.materialCount+1):
        print(i)
        MatColorString.append(StringVar())
        MatColorString[i].set(toHex(tuple(scene.getMaterialInfo(i,1))))
        m_type = matType[scene.getMaterialInfo(i,0)]

        MatTypeLabel.append(ttk.Label(MatTab, text=m_type))
        MatTypeLabel[i].grid(column=0, row=i,padx = "5",sticky="w")

        MatTypeSelectors.append(ttk.Spinbox(MatTab,from_=0, to=3,command = partial(updateMatType,i)))
        MatTypeSelectors[i].set(int(scene.getMaterialInfo(i,0)))
        MatTypeSelectors[i].grid(column=1, row=i,padx = "5",sticky="w")

        MatButtons.append(Button(MatTab, text='Color',command =  partial(colorPicker,MatColorString[i].get(),i),bg = MatColorString[i].get()))
        MatButtons[i].grid(column = 2, row=i,padx = "5",sticky="w")

except IOError as error:
    print("no MaterialData file found, hit render to create it")




sceneFilePathText_label = ttk.Label(SceneTab, text="scene file path : ").grid(column=0, row=0,padx = "5",sticky="w")
sceneFilePath_label = ttk.Label(SceneTab, textvariable=sceneFilePath,relief="sunken",borderwidth = 5).grid(column=1, row=0,padx = "5",sticky="w")
sceneFilePath_button = ttk.Button(SceneTab, text='Browse', command=openObjFile).grid(column=2, row=0,padx = "5",sticky="e")

tabPannel.add(SceneTab, text="Scene")
tabPannel.add(MatTab, text="Material")
tabPannel.pack(expand=1,fill="both")

#-----------------------------
#Bot Side
#-----------------------------

#Console output
render_button=ttk.Button(Bot_frame, text='Render', command=render).pack(anchor=S,padx=10, pady=10,fill='both')

Console = Text(Bot_frame,bg='black',fg='white')
Console.pack(anchor=S,padx=10, pady=10,fill='both')
redir=RedirectText(Console)
sys.stdout = redir

#-----------------------------
#Left Top Side
#-----------------------------
#.grid(column=0, row=1,columnspan=3,pady = "5",padx = "5",sticky="nsew")
#render button

#-----------------------------
#Right Top Side
#-----------------------------
load = Image.open("output/out.png")
outputImg = ImageTk.PhotoImage(load)

RenderImage_Label = ttk.Label(right_frame,image = outputImg)
RenderImage_Label.pack(padx=10, pady=10)

#-----------------------------
#    keyboard shortcuts
#-----------------------------
root.bind("<Return>", render)
root.mainloop()

