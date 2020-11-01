import pyopencl as cl
import numpy as np

class KernelLauncher(object):

    def __init__(self,context,platform,device,queue):
        #          Context
        # --------------------------
        self.platform = platform
        self.device = device
        self.context = context
        self.queue = queue

        #          Kernels
        # --------------------------
        # kernel ImgProcessing
        kernelsource = open('Kernels/ImgProcessing.c').read()
        program1 = cl.Program(context, kernelsource).build()
        self.K_ImgProcessing = program1.ImgProcessing
        self.K_ImgProcessing.set_scalar_arg_dtypes([None, None, np.uint32])

    def launch_ImgProcessing(self,h_src,h_out,SIZE):

        #         device buffers
        # --------------------------
        # img src
        d_src = cl.Buffer(self.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=h_src)
        # img out
        d_out = cl.Buffer(self.context, cl.mem_flags.WRITE_ONLY, h_out.nbytes)

        # exec K_imgProcessing for gamma and dynamic range
        self.K_ImgProcessing(self.queue, h_src.shape, None, d_src, d_out,SIZE*SIZE*3)
        cl.enqueue_copy(self.queue, h_out, d_out)