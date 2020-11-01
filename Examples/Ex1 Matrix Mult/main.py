import pyopencl as cl
import numpy as np
import deviceinfo
from time import time

#exec(open("main.py").read())
# --------------------------#
#         settings
# --------------------------#
SIZE = 1024
# --------------------------#
#     context and kernel
# --------------------------#
# Create a compute context
platform = cl.get_platforms()[0]    # Select the first platform [0]
# Select the first device on this platform [0]
device = platform.get_devices()[0]
context = cl.Context([device])      # Create a context with your device
# Create a command queue
queue = cl.CommandQueue(context)
deviceinfo.output_device_info(device)
#---------------
# kernel 1
kernelsource = open('Matrix_Naive.c').read()
# Create the compute program from the source buffer and build it
program1 = cl.Program(context, kernelsource).build()
#arg types
kernel1 = program1.kernel1
kernel1.set_scalar_arg_dtypes([None, None, None, np.uint32])

#---------------
# kernel 2
kernelsource = open('Matrix_WorkGroups.c').read()
# Create the compute program from the source buffer and build it
program2 = cl.Program(context, kernelsource).build()
#arg types
kernel2 = program2.kernel2
kernel2.set_scalar_arg_dtypes([None, None, None, np.uint32])

#---------------
# kernel 3
kernelsource = open('Matrix_WorkGroups_Private.c').read()
# Create the compute program from the source buffer and build it
program3 = cl.Program(context, kernelsource).build()
#arg types
kernel3 = program3.kernel3
kernel3.set_scalar_arg_dtypes([None, None, None, np.uint32])
#--------------------------------#
#         host buffers
#--------------------------------#
# Create a and b vectors and fill with random float values
h_a = np.random.rand(SIZE*SIZE).astype(np.float32)
h_b = np.random.rand(SIZE*SIZE).astype(np.float32)
# Create an empty c vector (a+b) to be returned from the compute device
h_c = np.empty(SIZE*SIZE).astype(np.float32)

#--------------------------------#
#         device buffers
#--------------------------------#
# Create the input (a, b) arrays in device memory and copy data from host
d_a = cl.Buffer(context, cl.mem_flags.READ_ONLY |
                cl.mem_flags.COPY_HOST_PTR, hostbuf=h_a)
d_b = cl.Buffer(context, cl.mem_flags.READ_ONLY |
                cl.mem_flags.COPY_HOST_PTR, hostbuf=h_b)
# Create the output (c) array in device memory
d_c = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, h_c.nbytes)


print("#--------------------------#")
print("#       Execution Time     #")
print("#--------------------------#\n")

#--------------------------------#
#       execution Kernel 1
#--------------------------------#
timeD = time()

kernel1(queue, (SIZE,SIZE), None, d_a, d_b, d_c, SIZE)
timeKernel1 = time() - timeD
#cl.enqueue_copy(queue, h_c, d_c)
print("kernel 1 (naive) time : " + str(timeKernel1))

#--------------------------------#
#       execution Kernel 2
#--------------------------------#
timeD = time()

kernel2(queue, (SIZE,), (64,), d_a, d_b, d_c, SIZE)
timeKernel2 = time() - timeD
#cl.enqueue_copy(queue, h_c, d_c)
print("kernel 2 (workgroups) time : " + str(timeKernel2))

#--------------------------------#
#       execution Kernel 3
#--------------------------------#
timeD = time()

kernel3(queue, (SIZE,), (64,), d_a, d_b, d_c, SIZE)
timeKernel3 = time() - timeD
#cl.enqueue_copy(queue, h_c, d_c)
print("kernel 3 (workgroups and row in private memory) time : " + str(timeKernel3))

#--------------------------------#
#       execution CPU
#--------------------------------#
a = h_a.reshape((SIZE,SIZE))
b = h_b.reshape((SIZE,SIZE))
c = h_c.reshape((SIZE,SIZE))
timeD = time()
result = np.matmul(a,b)
timeCPU = time() - timeD
print("CPU time : " + str(timeCPU))

print("#--------------------------#")
print("#         results          #")
print("#--------------------------#\n")

#print(np.linalg.norm(result,2))
print("Kernel 1 (naive) time = " + "{:10.0f}".format(timeCPU/timeKernel1) + " times faster than CPU")
print("Kernel 2 (workgroups) time = " + "{:10.0f}".format(timeCPU/timeKernel2) + " times faster than CPU")
print("Kernel 3 (workgroups and row in private memory) time = " + "{:10.0f}".format(timeCPU/timeKernel3) + " times faster than CPU")
