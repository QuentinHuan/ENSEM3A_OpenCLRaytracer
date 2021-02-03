import pyopencl as cl
import numpy as np
import os


class KernelLauncher(object):

    def __init__(self, context, platform, device, queue):
        #          Context
        # --------------------------
        os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'
        self.platform = platform
        self.device = device
        self.context = context
        self.queue = queue

        #          Kernels
        # --------------------------
        # kernel ImgProcessing
        kernelsource = open('Kernels/ImgProcessing.cl').read()
        program1 = cl.Program(context, kernelsource).build()
        self.K_ImgProcessing = program1.ImgProcessing
        self.K_ImgProcessing.set_scalar_arg_dtypes([None, None, np.uint32])

        # kernel RayTracing
        kernelsource = open('Kernels/Raytracing.cl').read()
        RaytracerProgram = cl.Program(context, kernelsource)
        RaytracerProgram = RaytracerProgram.build(options=['-I', "Kernels"])
        self.K_Raytracing = RaytracerProgram.Raytracing
        self.K_Raytracing.set_scalar_arg_dtypes(
            [None, None, None, None, None, None, None ,None,None ,None, np.uint32,np.uint32, np.uint32, np.uint32, np.uint32, None])

    def launch_Raytracing(self, h_img_out, h_vertex_p,h_vertex_n,h_vertex_uv, h_face_data, h_material_data,h_light_data, h_BVH, h_cam, h_envData, imgDim,spp,maxBounce,h_IBL):

        #         device buffers
        # --------------------------
        # img out
        d_img_out = cl.Buffer(
            self.context, cl.mem_flags.WRITE_ONLY, h_img_out.nbytes)
        # vertex data
        d_vertex_p = cl.Buffer(
            self.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=h_vertex_p)
        d_vertex_n = cl.Buffer(
            self.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=h_vertex_n)
        d_vertex_uv = cl.Buffer(
            self.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=h_vertex_uv)
        # face data
        d_face_data = cl.Buffer(self.context, cl.mem_flags.READ_ONLY |
                                cl.mem_flags.COPY_HOST_PTR, hostbuf=h_face_data)
        # material data
        d_material_data = cl.Buffer(
            self.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=h_material_data)
        d_BVH = cl.Buffer(
            self.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=h_BVH)
        # Camera
        d_cam = cl.Buffer(self.context, cl.mem_flags.READ_ONLY |
                          cl.mem_flags.COPY_HOST_PTR, hostbuf=h_cam)

        #environnement
        d_envData = cl.Buffer(self.context, cl.mem_flags.READ_ONLY |
                          cl.mem_flags.COPY_HOST_PTR, hostbuf=h_envData)

        #light
        if(len(h_light_data)==0):
            d_lightData = cl.Buffer(self.context, cl.mem_flags.READ_ONLY |
                          cl.mem_flags.COPY_HOST_PTR, hostbuf=np.array([0]))
        else:
            d_lightData = cl.Buffer(self.context, cl.mem_flags.READ_ONLY |
                            cl.mem_flags.COPY_HOST_PTR, hostbuf=h_light_data)
        #IBL
        fmt = cl.ImageFormat(cl.channel_order.RGBA, cl.channel_type.UNORM_INT8)
        d_IBL = cl.Image(self.context, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,fmt,h_IBL.size,None,h_IBL.tobytes())

        triCount = int(len(h_face_data)/10)
        lightCount = int(len(h_light_data))
        self.K_Raytracing(self.queue, (imgDim,), None, d_img_out, d_vertex_p, d_vertex_n, d_vertex_uv, d_face_data,d_lightData,
                          d_material_data, d_BVH, d_cam, d_envData, triCount,lightCount, imgDim, spp, maxBounce, d_IBL)
        cl.enqueue_copy(self.queue, h_img_out, d_img_out)

        d_img_out.release()
        d_vertex_p.release()
        d_vertex_n.release()
        d_vertex_uv.release()
        d_face_data.release()
        d_material_data.release()
        d_BVH.release()
        d_cam.release()


    def launch_ImgProcessing(self, h_src, h_out, SIZE):

        #         device buffers
        # --------------------------
        # img src
        d_src = cl.Buffer(self.context, cl.mem_flags.READ_ONLY |
                          cl.mem_flags.COPY_HOST_PTR, hostbuf=h_src)
        # img out
        d_out = cl.Buffer(self.context, cl.mem_flags.WRITE_ONLY, h_out.nbytes)

        # exec K_imgProcessing for gamma and dynamic range
        self.K_ImgProcessing(self.queue, h_src.shape,
                             None, d_src, d_out, SIZE*SIZE*3)
        cl.enqueue_copy(self.queue, h_out, d_out)
