import tkinter as tk
from tkinter import ttk
from tkinter import  StringVar


class ScrollableFrame(ttk.Frame):
    def __init__(self, container,bg, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        #scroll bar
        self.bg = bg
        self.canvas = tk.Canvas(container,highlightthickness=0, highlightbackground=self.bg,background = self.bg)
        self.scroll_y = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.frame = ttk.Frame(self.canvas)

        # put the frame in the canvas
        self.canvas_frame = self.canvas.create_window(0, 0, anchor='nw', window=self.frame)
        # make sure everything is displayed before configuring the scrollregion
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'), yscrollcommand=self.scroll_y.set)
                        
        self.canvas.pack(fill='both', expand=True, side='left')
        self.scroll_y.pack(fill='y', side='right', padx="5")

        self.frame.bind("<Configure>", self.OnFrameConfigure)
        self.canvas.bind('<Configure>', self.FrameWidth)


    def FrameWidth(self,event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width = canvas_width)

    def OnFrameConfigure(self,event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"),highlightthickness=0, highlightbackground=self.bg,background = self.bg)

class param_Entry(ttk.Frame):
     def __init__(self,camTab, parameters, paramName,column,row, *args, **kwargs):
        self.textVariable = StringVar()
        self.textVariable.set(parameters[paramName])
        self.entry = ttk.Entry(camTab,textvariable = self.textVariable)
        self.entry.grid(column=column, row=row,padx = "5",pady = "1",sticky="w")