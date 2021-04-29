# ENSEM3A_OpenCLRaytracer
3rd year project : GPU accelerated raytracing engine

This is a retake on my previous project: https://github.com/QuentinHuan/FSCppRaytracer
Last version was more of a prototype and wasn't really usable in practice. The goal here is to make a usable piece of software, with a UI.

Technologies: PyOpenCL, Tkinter

![alt text](/screenshots/screenshot.png)

Features :

-Diffuse, Glossy and Transparent materials [DONE (but can be improved)]

-BVH acceleration structure

-material and lighting editing in UI

-Image based lighting 

![alt text](/screenshots/IBL.png)

![alt text](/screenshots/Serre.png)

29/04/2021 notes:

The software is usable in practice, but lacks a lot of features and is subjet to fairly strong limitations. Mainly :

-> The BVH tree construction was made on the CPU with Python in a quite naive way, which proved to be a bad idea: reimplementing this piece of code in C (or using Python properly !!) should speed up this part by a great amount. Right now, this is the main bottleneck preventing using the Engine with more detailed scenes (current program already struggle with only 10k triangles on my computer)

-> no Importance Sampling techniques implemented: this makes rendering of reflective surfaces challenging. Implementing multiple importance sampling strategies would also make the engine more versatile at rendering variety of scenes and materials.

-> no UV texturing: this is a quite big limitation in practice

