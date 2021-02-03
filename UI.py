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
from UI_elements import ScrollableFrame
from UI_elements import param_Entry
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
        #filename = file.name.replace(".ini",".obj")
        f.write("scenePath="+file.name)
        f.close()

        scene = Scene(file.name,False)
        return NONE
    else:
        print("no .obj file")
        return NONE

#Explorer Widget
#get the path the .obj file to render, store it in 'sceneFilePath'
#save the path in the file 'config.ini' for next time
def openIBLFile(*args):
    global scene
    file = askopenfile(mode ='r', filetypes =[('jpg files', '*.jpg')]) 
    if file is not None: 
        IBLFilePath.set(file.name)
        scene.config.setParameter("IBLfile",file.name)
        updateParameters()
        f.close()
        return NONE
    else:
        print("no .jpg file")
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
    scene = Scene(path,True)

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
    #render settings
    scene.config.setParameter("resolution",resolution_Entry.get())
    scene.config.setParameter("spp",spp_Entry.get())
    scene.config.setParameter("maxBounce",maxBounce_Entry.get())

    #camera settings
    scene.config.setParameter("cam_x",x_Entry.entry.get())
    scene.config.setParameter("cam_y",y_Entry.entry.get())
    scene.config.setParameter("cam_z",z_Entry.entry.get())

    scene.config.setParameter("cam_rx",rx_Entry.entry.get())
    scene.config.setParameter("cam_ry",ry_Entry.entry.get())
    scene.config.setParameter("cam_rz",rz_Entry.entry.get())

    scene.config.setParameter("cam_DOF",DOF_Entry.entry.get())

    scene.config.setParameter("IBL_Power",IBL_Power_Entry.entry.get())

    scene.config.setParameter("sun_rx",dx_Sun_Entry.entry.get())
    scene.config.setParameter("sun_ry",dy_Sun_Entry.entry.get())
    scene.config.setParameter("sun_rz",dz_Sun_Entry.entry.get())
    scene.config.setParameter("sun_Power",Sun_Power_Entry.entry.get())

    for i in range(len(MatParamEntry)):
        #get alpha entry value
        scene.config.setParameter("M_"+str(i)+"_roughness",float(MatParamEntry[i].get()))

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

scene = Scene(scenePath,False)

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

    #color
    MatColorString = []
    MatButtons = []
    #type selector
    MatTypeLabel = []
    MatTypeSelectors = []
    #parameter
    MatParamEntry = []
    MatParamLabel = []
    MatParamString = []

    scrollFrame.frame.columnconfigure(0, weight=1)
    scrollFrame.frame.columnconfigure(1, weight=1)
    scrollFrame.frame.columnconfigure(2, weight=1)
    scrollFrame.frame.columnconfigure(3, weight=1)

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

        #param entry
        MatParamString.append(StringVar())
        MatParamString[i].set(parameters["M_"+str(i)+"_roughness"])
        MatParamLabel.append(ttk.Label(scrollFrame.frame, text="alpha : "))
        MatParamEntry.append(ttk.Entry(scrollFrame.frame,textvariable = MatParamString[i]))
        MatParamEntry[i].grid(column=4, row=i,padx = "1",pady = "1",sticky=NSEW)
        MatParamLabel[i].grid(column=3, row=i,padx = "1",pady = "1",sticky=NSEW)

        #color button
        MatButtons.append(Button(scrollFrame.frame, text='Color',command =  partial(colorPicker,MatColorString[i].get(),i),bg = MatColorString[i].get(),highlightthickness=1, highlightbackground="black"))
        MatButtons[i].grid(column = 2, row=i,padx = "1",pady = "1",sticky=NSEW)

except IOError as error:
    print("no MaterialData file found, hit render to create it")


#scene Tab
#-----------------------------------
#browse object button
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

#Camera Tab
#-----------------------------------
#scroll bar
CamTab = ttk.Frame(tabPannel)

position_Text_label = ttk.Label(CamTab, text="position (X,Y,Z) : ")
position_Text_label.grid(column=0, row=0,padx = "5",pady = "1",sticky="w")

x_Entry = param_Entry(CamTab,parameters,"cam_x",1,0)
y_Entry = param_Entry(CamTab,parameters,"cam_y",2,0)
z_Entry = param_Entry(CamTab,parameters,"cam_z",3,0)

orientation_Text_label = ttk.Label(CamTab, text="orientation (X,Y,Z) : ")
orientation_Text_label.grid(column=0, row=1,padx = "5",pady = "1",sticky="w")

rx_Entry = param_Entry(CamTab,parameters,"cam_rx",1,1)
ry_Entry = param_Entry(CamTab,parameters,"cam_ry",2,1)
rz_Entry = param_Entry(CamTab,parameters,"cam_rz",3,1)

DOF_Text_label = ttk.Label(CamTab, text="Depth of field : ")
DOF_Text_label.grid(column=0, row=2,padx = "5",pady = "1",sticky="w")

DOF_Entry = param_Entry(CamTab,parameters,"cam_DOF",1,2)

#Environnement Tab
#-----------------------------------
EnvTab = ttk.Frame(tabPannel)

#IBL file
IBLFilePath = StringVar()
IBLFilePath.set(parameters["IBLfile"])
IBLFilePath_Text_label = ttk.Label(EnvTab, text="IBL file path : ").grid(column=0, row=0,padx = "5",pady = "1",sticky="w")
IBLFilePath_label = ttk.Label(EnvTab, textvariable=IBLFilePath,relief="sunken",borderwidth = 5).grid(column=1, row=0,padx = "5",pady = "1",sticky="w")
IBLFilePath_button = ttk.Button(EnvTab, text='Browse', command=openIBLFile).grid(column=2, row=0,padx = "5",pady = "1",sticky="w")

#IBL Power
IBL_Power_Text_label = ttk.Label(EnvTab, text="IBL Power : ")
IBL_Power_Text_label.grid(column=0, row=1,padx = "5",pady = "1",sticky="w")
IBL_Power_Entry = param_Entry(EnvTab,parameters,"IBL_Power",1,1)

#Sun Direction
Sun_dir_Text_label = ttk.Label(EnvTab, text="Sun direction (X,Y,Z) : ")
Sun_dir_Text_label.grid(column=0, row=2,padx = "5",pady = "1",sticky="w")

dx_Sun_Entry = param_Entry(EnvTab,parameters,"sun_rx",1,2)
dy_Sun_Entry = param_Entry(EnvTab,parameters,"sun_ry",2,2)
dz_Sun_Entry = param_Entry(EnvTab,parameters,"sun_rz",3,2)

#Sun Power
Sun_Power_Text_label = ttk.Label(EnvTab, text="Sun Power (X,Y,Z) : ")
Sun_Power_Text_label.grid(column=0, row=3,padx = "5",pady = "1",sticky="w")
Sun_Power_Entry = param_Entry(EnvTab,parameters,"sun_Power",1,3)

# add tabs
tabPannel.add(SceneTab, text="Scene")
tabPannel.add(CamTab, text="Camera")
tabPannel.add(EnvTab, text="Environement")
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


