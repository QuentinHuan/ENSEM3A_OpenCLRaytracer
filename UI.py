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
from scrollableFrame import ScrollableFrame
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

#clamp to 255
def clamp(x): 
    return max(0, min(x, 255))

# convert color (f,f,f) to hexadecimal
def toHex(colorToConvert):
    if(len(colorToConvert) == 3):
        r = int(colorToConvert[0]*255)
        g = int(colorToConvert[1]*255)
        b = int(colorToConvert[2]*255)
        return "#{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))

#-----------------------------
#      Button callbacks
#-----------------------------

#Explorer Widget
#get the path the .obj file to render, store it in 'sceneFilePath'
#save the path in the file 'config.ini' for next time
def openObjFile(*args):
    global scene
    file = askopenfile(mode ='r', filetypes =[('Obj files', '*.obj')]) 
    if file is not None: 
        #config.setParameter("scenePath", file.name)
        #updateParameters()
        sceneFilePath.set(file.name)
        f = open("config.ini","w")
        f.write("scenePath="+file.name)
        f.close()

        scene = Scene(file.name)
        return NONE
    else:
        print("no .obj file")
        return NONE

#reload parameters from file
def updateParameters():
    global parameters
    parameters = scene.loadParameters()

#render the scene at 'sceneFilePath' using the main script
def render(*args):
    global RenderImage_Label
    arg_Callback()
    path = parameters["sceneFile"]
    print("ask to renderer scene '" + path + "'")
    scene = Scene(path)

    main(scene)
    load = Image.open("output/out.png")
    outputImg = ImageTk.PhotoImage(load)
    RenderImage_Label.configure(image=outputImg)
    RenderImage_Label.image = outputImg

# color picker dialog, write change to disk
def colorPicker(previousColor,matId):
    global pickedColor
    global MatButtons
    pickedColor = colorchooser.askcolor(MatButtons[matId].cget('bg'))
    out = [0,0,0]
    for i in range(3):
        out[i] = min(pickedColor[0][i]/255.0,1.0)
    print("pickedColor =" + str(out) + "HEX = " + pickedColor[1])
    scene.config.setParameter("M_"+str(matId)+"_Color_R",out[0])
    scene.config.setParameter("M_"+str(matId)+"_Color_G",out[1])
    scene.config.setParameter("M_"+str(matId)+"_Color_B",out[2])
    updateParameters()
    MatButtons[matId].configure(background = pickedColor[1])

#update material info and write changes to disk
def Material_Spinbox_Callback(matId):
    global MatTypeSelectors
    global MatTypeLabel
    global matType
    #get spinbox value
    scene.config.setParameter("M_"+str(matId)+"_Type",int(MatTypeSelectors[matId].get()))
    #update spinbox textLabel
    MatTypeLabel[matId].configure(text= matType[int(MatTypeSelectors[matId].get())])

#update material info and write changes to disk
def arg_Callback(*args):
    #get entry values
    scene.config.setParameter("resolution",resolution_Entry.get())
    scene.config.setParameter("spp",spp_Entry.get())
    scene.config.setParameter("maxBounce",maxBounce_Entry.get())

#-----------------------------
#           Init
#-----------------------------
root = Tk()
root.tk.call('lappend', 'auto_path', 'awthemes-9.5.0')
root.tk.call('package', 'require', 'awdark')
style = ttk.Style()
ttk.Style().theme_use('awdark')
root.title("OpenCL Raytracer")
#background color
bg = style.lookup('TFrame', 'background')

#configReader Object
f = open("config.ini","r")
scenePath = f.readline().split("=")[1]
#load and build scene
scene = Scene(scenePath)
#load config
config = scene.config
parameters = {}
updateParameters()



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

#-----------------------------------
#Left Top Side || configuration tab
#-----------------------------------

tabPannel = ttk.Notebook(left_Top_frame)
SceneTab = ttk.Frame(tabPannel)

#Material Tab
#-----------------------------------
#scroll bar
MatTab = ttk.Frame(tabPannel)
#MatTab.pack(fill='both', expand=True, side='left', padx = 0)

scrollFrame = ScrollableFrame(MatTab,bg)

try:
    MatTypeLabel = []
    MatColorString = []
    MatButtons = []
    MatTypeSelectors = []

    scrollFrame.frame.columnconfigure(0, weight=1)
    scrollFrame.frame.columnconfigure(1, weight=1)
    scrollFrame.frame.columnconfigure(2, weight=1)

    for i in range(scene.materialCount+1):

        scrollFrame.frame.rowconfigure(i, weight=1)

        MatColorString.append(StringVar())
        MatColorString[i].set(toHex((float(parameters["M_"+str(i)+"_Color_R"]),float(parameters["M_"+str(i)+"_Color_G"]),float(parameters["M_"+str(i)+"_Color_B"]))))
        m_type_int = int(parameters["M_"+str(i)+"_Type"])
        m_type_str = matType[m_type_int]

        #type label
        MatTypeLabel.append(ttk.Label(scrollFrame.frame, text=m_type_str))
        MatTypeLabel[i].grid(column=0, row=i,padx = "1",pady = "1",sticky=NSEW)

        #type spinBox
        MatTypeSelectors.append(ttk.Spinbox(scrollFrame.frame,from_=0, to=3,command = partial(Material_Spinbox_Callback,i)))
        MatTypeSelectors[i].set(MatColorString)
        MatTypeSelectors[i].set(int(parameters["M_"+str(i)+"_Type"]))
        MatTypeSelectors[i].grid(column=1, row=i,padx = "1",pady = "1",sticky=NSEW)

        #color button
        MatButtons.append(Button(scrollFrame.frame, text='Color',command =  partial(colorPicker,MatColorString[i].get(),i),bg = MatColorString[i].get(),highlightthickness=1, highlightbackground="black"))
        MatButtons[i].grid(column = 2, row=i,padx = "1",pady = "1",sticky=NSEW)

except IOError as error:
    print("no MaterialData file found, hit render to create it")


#scene Tab
#-----------------------------------
sceneFilePath = StringVar()
sceneFilePath.set(parameters["sceneFile"])
sceneFilePath_Text_label = ttk.Label(SceneTab, text="scene file path : ").grid(column=0, row=0,padx = "5",pady = "1",sticky="w")
sceneFilePath_label = ttk.Label(SceneTab, textvariable=sceneFilePath,relief="sunken",borderwidth = 5).grid(column=1, row=0,padx = "5",pady = "1",sticky="w")
sceneFilePath_button = ttk.Button(SceneTab, text='Browse', command=openObjFile).grid(column=2, row=0,padx = "5",pady = "1",sticky="e")

#resolution entry
resolution_textVariable = StringVar()
resolution_textVariable.set(parameters["resolution"])
resolution_Text_label = ttk.Label(SceneTab, text="resolution : ").grid(column=0, row=1,padx = "5",pady = "1",sticky="w")
resolution_Entry = ttk.Entry(SceneTab,textvariable = resolution_textVariable)
resolution_Entry.grid(column=1, row=1,padx = "5",pady = "1",sticky="w")

#spp entry
spp_textVariable = StringVar()
spp_textVariable.set(parameters["spp"])
spp_Text_label = ttk.Label(SceneTab, text="sample per pixel : ").grid(column=0, row=2,padx = "5",pady = "1",sticky="w")
spp_Entry = ttk.Entry(SceneTab,textvariable = spp_textVariable)
spp_Entry.grid(column=1, row=2,padx = "5",pady = "1",sticky="w")

#maxBounce entry
maxBounce_textVariable = StringVar()
maxBounce_textVariable.set(parameters["maxBounce"])
maxBounce_Text_label = ttk.Label(SceneTab, text="maximum bounce : ").grid(column=0, row=3,padx = "5",pady = "1",sticky="w")
maxBounce_Entry = ttk.Entry(SceneTab,textvariable = maxBounce_textVariable)
maxBounce_Entry.grid(column=1, row=3,padx = "5",pady = "1",sticky="w")



tabPannel.add(SceneTab, text="Scene")
tabPannel.add(MatTab, text="Material")
tabPannel.pack(expand=1,fill="both")

#-----------------------------
#    Bot Side | console
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
#Right Top Side | Image output
#-----------------------------
load = Image.open("output/out.png")
outputImg = ImageTk.PhotoImage(load)

RenderImage_Label = ttk.Label(right_frame,image = outputImg)
RenderImage_Label.pack(padx=10, pady=10)

#-----------------------------
#    keyboard shortcuts
#-----------------------------
root.bind("<Return>", arg_Callback)
root.mainloop()


