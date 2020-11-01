from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfile 
import sys
from subprocess import Popen, PIPE
from PIL import Image, ImageTk

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

#-----------------------------
#      Button callbacks
#-----------------------------

#get the path the .obj file to render, store it in 'sceneFilePath'
#save the path in the file 'config.ini' for next time
def openObjFile(*args):
    file = askopenfile(mode ='r', filetypes =[('Obj files', '*.obj')]) 
    if file is not None: 
        content = file.read() 
        sceneFilePath.set(file.name)
        file.close()
        configFile = open("config.ini",mode='w')
        configFile.write("sceneFile=" + sceneFilePath.get())
        configFile.close()
        return content
    else:
        print("no .obj file")
        return NONE

#render the scene at 'sceneFilePath' using the main script
def render(*args):
    path = sceneFilePath.get().split("/")
    sceneName = path[len(path)-1]
    print("ask for renderering scene '" + sceneName + "'")

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

#Left and Right Frame x | x
left_frame = ttk.Labelframe(mainframe,text="Render Settings",padding="5 5 5 5")
left_frame.pack(side="left",fill='both',padx=5)
right_frame = ttk.Labelframe(mainframe,text="Output Image")
right_frame.pack(side="right",fill='both',padx=5)

#Divide left in Top and Bottom
left_Top_frame = ttk.Label(left_frame)
left_Top_frame.pack(side="top",fill="x")
left_Top_frame.rowconfigure(0,weight=1)
left_Top_frame.rowconfigure(1,weight=1)
left_Top_frame.columnconfigure(0,weight=1)
left_Top_frame.columnconfigure(1,weight=1)
left_Top_frame.columnconfigure(2,weight=1)

left_Bot_frame = ttk.Labelframe(left_frame,text='Console')
left_Bot_frame.pack(side="bottom")

#-----------------------------
#Left Top Side
#-----------------------------
#.obj file Selection 


sceneFilePathText_label = ttk.Label(left_Top_frame, text="scene file path : ").grid(column=0, row=0,padx = "5",sticky="w")
sceneFilePath_label = ttk.Label(left_Top_frame, textvariable=sceneFilePath,relief="sunken",borderwidth = 5).grid(column=1, row=0,padx = "5",sticky="w")
sceneFilePath_button = ttk.Button(left_Top_frame, text='Browse', command=openObjFile).grid(column=2, row=0,padx = "5",sticky="e")

#render button
render_button=ttk.Button(left_Top_frame, text='Render', command=render).grid(column=0, row=1,columnspan=3,pady = "5",padx = "5",sticky="nsew")

#-----------------------------
#Left Bot Side
#-----------------------------
#Console output
Console = Text(left_Bot_frame,bg='black',fg='white')
Console.pack(anchor=S,padx=10, pady=10,fill='both')
redir=RedirectText(Console)
sys.stdout = redir

#-----------------------------
#Right Side
#-----------------------------
load = Image.open("output/test.png")
outputImg = ImageTk.PhotoImage(load)

RenderImage_Label = ttk.Label(right_frame,image = outputImg)
RenderImage_Label.image = render
RenderImage_Label.pack(padx=10, pady=10)

#-----------------------------
#    keyboard shortcuts
#-----------------------------
root.bind("<Return>", render)
root.mainloop()

