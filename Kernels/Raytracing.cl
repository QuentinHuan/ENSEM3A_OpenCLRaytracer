#include "MathLib.cl"

// helper function
// extract material data into a more convenient data structure
material extractMaterial(__global float *mat, int index) {

  material m;
  m.type = mat[index * 6 + 0];
  m.color =
      (float3)(mat[index * 6 + 1], mat[index * 6 + 2], mat[index * 6 + 3]);
  m.roughness = mat[index * 6 + 4];
  m.ior = mat[index * 6 + 5];

  return m;
}

//generate a camera ray from cam array and pixel position
ray genCameraRay(int i, __global float *cam)
{
    ray r;
    int pixelY = (i + 1) % (int)cam[6];
    int pixelX = (i - pixelY) / (int)cam[6];
    float3 focal =
        (float3)(cam[0], cam[1] - (1.0f / (2.0f * tan(cam[9] / 2.0f))), cam[2]);
    float3 position = (float3)(cam[0], cam[1], cam[2]);

    float pasX = 1.0 / cam[6];
    float pasY = pasX;
    float3 pixelCoord = (float3)(pixelY * pasY - 0.5f, 0, 0.5f - pixelX * pasX);

    r.o = position;
    r.dir = normalize((position + pixelCoord) - focal);
    r.dir = rotateVec(cam[3]*(3.14f/180.0f),(float3)(1,0,0),r.dir); // x angle
    r.dir = rotateVec(cam[4]*(3.14f/180.0f),(float3)(0,1,0),r.dir); // y angle
    r.dir = rotateVec(cam[5]*(3.14f/180.0f),(float3)(0,0,1),r.dir); // z angle
    return r;
}

float3 naiveGI(float3 sampleOut,int maxBounce,int triCount,hitInfo H_cam, ray R_cam, material camMat,__read_only image2d_t IBL,const sampler_t sampler,  __global float *mat,
__constant float *vertex_p, __constant float *vertex_n, __constant float *vertex_uv, __constant int *face_data,__constant float *BVH,
 unsigned int* seed0,  unsigned int* seed1)
{
        // camRay is the previous ray
        // bounce ray the new ray that bounce of the surface
        //for each bounce
        for (int j = 0; j <= maxBounce; j++) // max bounce limit
        {
            if (H_cam.bHit)//hit something
            {
                // bounce Ray
                if (camMat.type != 0)//not lightsource
                {
                    // next ray generation
                    ray R_bounce;
                    float3 BRDF;
                    float invPdfBounce;
                    //sampling method selection depending on current surface material
                    switch(camMat.type)
                    {
                        case 0://emissive
                            R_bounce.dir = rand_hemi_uniform(H_cam.n, seed1, seed0, &invPdfBounce);
                            BRDF = (float3)(1,1,1);
                            break;
                        case 1://diffuse
                            R_bounce.dir = rand_hemi_cosine(H_cam.n, seed1, seed0, &invPdfBounce);
                            BRDF = BRDF_Lambert(camMat);
                            break;
                        case 2://Glossy GGX
                            R_bounce.dir = rand_sample_GGX(camMat, R_cam.dir, H_cam.n, seed1, seed0, &invPdfBounce);
                            BRDF = BRDF_GGX(camMat,-R_cam.dir,R_bounce.dir,H_cam.n);
                            break;
                        case 3://Glass
                            R_bounce.dir = rand_sample_Glass(R_cam.dir, &invPdfBounce);
                            BRDF = BRDF_Glass(camMat);
                            invPdfBounce = (1.0f)/fabs(dot(R_bounce.dir, normalize(H_cam.n)));
                            break;
                    }
                    R_bounce.o = (R_cam.o + (normalize(R_cam.dir) * H_cam.k));

                    // next ray shoot
                    hitInfo H_bounce = rayTrace(R_bounce, vertex_p, vertex_n, vertex_uv, face_data, triCount,BVH);
                    material bounceMat = extractMaterial(mat, H_bounce.mat);

                    //compute attenuation
                    float att = invPdfBounce * fabs(dot(R_bounce.dir, normalize(H_cam.n)));

                    if (H_bounce.bHit) // hit something solid
                    {
                        //swap bounce and cam ray
                        R_cam = R_bounce;
                        H_cam = H_bounce;
                        camMat = bounceMat;
                        //take bounce contribution into account
                        sampleOut = sampleOut * BRDF * att;
                        if (bounceMat.type != 0) //not emissive surface
                        {
                            //max bounce reach, sample is nullified
                            if (j == maxBounce) 
                            {
                                sampleOut = 0;
                                break;
                            }
                        } 
                        else //emissive surface
                        {
                            sampleOut = sampleOut * bounceMat.roughness;//take alpha as emissive power
                            break;
                        }
                    } 
                    else // lost in background
                    {
                        sampleOut = sampleOut*sampleIBL(R_bounce.dir,sampler,IBL);//sample IBL for background
                        break;
                    }
                } 
                else break;
            } 
            else break;
        }
        return sampleOut;
}


float3 GI(float3 sampleOut,int maxBounce,int triCount,hitInfo H_cam, ray R_cam, material camMat,__read_only image2d_t IBL,const sampler_t sampler,  __global float *mat,
__constant float *vertex_p, __constant float *vertex_n, __constant float *vertex_uv, __constant int *face_data,const int lightCount,__constant int *light_data,__constant float *BVH,
 unsigned int* seed0,  unsigned int* seed1)
{
        // camRay is the previous ray
        // bounce ray the new ray that bounce of the surface
        //for each bounce
        for (int j = 0; j <= maxBounce; j++) // max bounce limit
        {
            if (H_cam.bHit)//hit something
            {
                // bounce Ray
                if (camMat.type != 0)//not lightsource
                {
                    // next ray generation
                    ray R_bounce;
                    float3 BRDF;
                    float invPdfBounce;
                    //sampling method selection depending on current surface material
                    switch(camMat.type)
                    {
                        case 0://emissive
                            R_bounce.dir = rand_hemi_uniform(H_cam.n, seed1, seed0, &invPdfBounce);
                            BRDF = (float3)(1,1,1);
                            break;
                        case 1://diffuse
                            R_bounce.dir = rand_hemi_cosine(H_cam.n, seed1, seed0, &invPdfBounce);
                            BRDF = BRDF_Lambert(camMat);
                            break;
                        case 2://Glossy GGX
                            //R_bounce.dir = rand_sample_GGX(camMat, R_cam.dir, H_cam.n, seed1, seed0, &invPdfBounce);
/*                             R_bounce.dir = sampleLight(R_cam.o + H_cam.k*R_cam.dir,vertex_p,vertex_n,vertex_uv,face_data,triCount,light_data,
                    lightCount,seed0,seed1,&invPdfBounce); */
                    R_bounce.dir = rand_hemi_uniform(H_cam.n, seed1, seed0, &invPdfBounce);
                            BRDF = BRDF_GGX(camMat,-R_cam.dir,R_bounce.dir,H_cam.n);
                            break;
                        case 3://Glass
                            R_bounce.dir = rand_sample_Glass(R_cam.dir, &invPdfBounce);
                            BRDF = BRDF_Glass(camMat);
                            invPdfBounce = (1.0f)/fabs(dot(R_bounce.dir, normalize(H_cam.n)));
                            break;
                    }
                    R_bounce.o = (R_cam.o + (normalize(R_cam.dir) * H_cam.k));

                    // next ray shoot
                    hitInfo H_bounce = rayTrace(R_bounce, vertex_p, vertex_n, vertex_uv, face_data, triCount,BVH);
                    material bounceMat = extractMaterial(mat, H_bounce.mat);

                    //compute attenuation
                    float att = invPdfBounce * fabs(dot(R_bounce.dir, normalize(H_cam.n)));

                    if (H_bounce.bHit) // hit something solid
                    {
                        //swap bounce and cam ray
                        R_cam = R_bounce;
                        H_cam = H_bounce;
                        camMat = bounceMat;
                        //take bounce contribution into account
                        sampleOut = sampleOut * BRDF * att;
                        
                        if (bounceMat.type != 0) //not emissive surface
                        {
                            //max bounce reach, sample is nullified
                            if (j == maxBounce) 
                            {
                                sampleOut = 0;
                                break;
                            }
                        } 
                        else //emissive surface
                        {
                            if(j>0) sampleOut = sampleOut * bounceMat.roughness;//take alpha as emissive power
                            break;
                        }
                    } 
                    else // lost in background
                    {
                        sampleOut = sampleOut*sampleIBL(R_bounce.dir,sampler,IBL);//sample IBL for background
                        break;
                    }
                } 
                else break;
            } 
            else break;
        }
        return sampleOut;
}

float3 DirectLight(float3 sampleOut,int maxBounce,int triCount,hitInfo H_cam, ray R_cam, material camMat,__read_only image2d_t IBL,const sampler_t sampler,  __global float *mat,
__constant float *vertex_p, __constant float *vertex_n, __constant float *vertex_uv, __constant int *face_data,__global float *envData,const int lightCount,__constant int *light_data,__constant float *BVH,
 unsigned int* seed0,  unsigned int* seed1)
{
        // camRay is the previous ray
        // bounce ray the new ray that bounce of the surface
        //for each bounce

            if (H_cam.bHit)//hit something
            {
                if (camMat.type != 0)//not lightsource
                {
                    float invPDF = 1.0f;
                    ray shadRay;
                    shadRay.o = R_cam.o + H_cam.k*R_cam.dir;
                    shadRay.dir = sampleLight(R_cam.o + H_cam.k*R_cam.dir,vertex_p,vertex_n,vertex_uv,face_data,triCount,
                    light_data,lightCount, seed1, seed0,&invPDF,envData);

                    hitInfo H_shadow = rayTrace(shadRay, vertex_p,vertex_n,vertex_uv,face_data,triCount,BVH);
                    material shadowMat = extractMaterial(mat, H_shadow.mat);
                    //printf("%f",shadRay.dir.x);
                    float3 BRDF = (float3)(1.0f);
                    switch(camMat.type)
                    {
                        case 0://emissive
                            BRDF = (float3)(1,1,1);
                            break;
                        case 1://diffuse
                            BRDF = BRDF_Lambert(camMat);
                            break;
                        case 2://Glossy GGX
                            BRDF = BRDF_GGX(camMat,-R_cam.dir,shadRay.dir,H_cam.n);
                            break;
                        case 3://Glass
                            BRDF = BRDF_Glass(camMat);
                            //invPDF = (1.0f)/fabs(dot(shadRay.dir, normalize(H_cam.n)));
                            break;
                    }

                    if (H_shadow.bHit)
                    {
                        if (shadowMat.type != 0)
                        {
                            return (float3)(0,0,0);
                        }
                        else
                        {
                            float3 light = shadowMat.color*shadowMat.roughness;
                            float nDotWi = fabs(dot(H_shadow.n, shadRay.dir));
                            
                            return  length(BRDF)*light*nDotWi*invPDF;
                        }
                    }
                    else
                    {
                        float nDotWi = fabs(dot(H_cam.n, shadRay.dir));
                        return nDotWi*length(BRDF)*invPDF;
                        //return (float3)(1);
                    }
                }
                else
                {
                    return (float3)(0);
                }
            }
        return sampleOut;
}


//------------------------------------
// raytracing kernel
// data and mat as defined in 'scene' class member 'vertexData' and
// 'materialData' cam --> the camera, [x,y,z,dx,dy,dz] out --> the output color
// []
__kernel void Raytracing(__global float *out, __constant float *vertex_p,
                         __constant float *vertex_n,
                         __constant float *vertex_uv, __constant int *face_data, __constant int *light_data,
                         __global float *mat,__constant float *BVH, __global float *cam,__global float *envData,
                         const int triCount,const int lightCount, const int imgSize,
                         const int maxSpp, const int maxBounce, __read_only image2d_t IBL) {
//--------------
//initialise
//--------------
    int i = get_global_id(0);//pixel coordinate
    unsigned int seed0 = i % imgSize;
    unsigned int seed1 = i / imgSize;
    unsigned int seed01 = i % imgSize;
    unsigned int seed11 = i / imgSize;
    //output color and current spp
    float3 output = (float3)(0.0f);
    int spp = 0;
    //IBL sampler
    const sampler_t sampler =  CLK_NORMALIZED_COORDS_FALSE | CLK_ADDRESS_CLAMP_TO_EDGE | CLK_FILTER_LINEAR;
//-----------------
// Ray construction
//-----------------
    //initial camera ray
    ray r = genCameraRay(i,cam);
    // fire cam ray
    hitInfo H_cam_cache = rayTrace(r, vertex_p, vertex_n, vertex_uv, face_data, triCount,BVH);
    material camMat_cache = extractMaterial(mat, H_cam_cache.mat);
//-----------------
// Raytracing logic
//-----------------
    while (spp < maxSpp) // for each sample
    {
        spp++;
        // load first ray and result from cache
        ray R_cam = r;//eye ray
        hitInfo H_cam = H_cam_cache;//eye ray result
        material camMat = camMat_cache;//eye ray material

        //sample out initialisation
        float3 baseColor = (float3)(1.0f);
        float3 GIColor = (float3)(1.0f);
        float3 directColor = (float3)(1.0f);
        if (H_cam.bHit)
        {
            baseColor = camMat.color; //if hit something initialise with base color;
        }
        else
        {
            baseColor = (float3)(1);
            directColor = (float3)(0);
            GIColor = sampleIBL(R_cam.dir,sampler,IBL); // initialise with background
        } 

/*         baseColor = naiveGI(baseColor,maxBounce,triCount,H_cam,R_cam, camMat,IBL,sampler, mat, vertex_p,
         vertex_n, vertex_uv, face_data, BVH,&seed0,&seed1); */

        directColor = DirectLight(directColor,maxBounce,triCount, H_cam,  R_cam, camMat, IBL, sampler, mat,
vertex_p, vertex_n, vertex_uv, face_data,envData,lightCount,light_data,BVH, &seed0, &seed1);

        GIColor = GI(GIColor, maxBounce, triCount, H_cam,  R_cam,  camMat,  IBL,  sampler,mat,
  vertex_p,   vertex_n,   vertex_uv, face_data,  lightCount,  light_data,  BVH,
 &seed01,   &seed11);

        //baseColor = GIcolor;
        output = output + baseColor*(directColor+GIColor) ;
    }
    //mean
    output = output / (float)(maxSpp);

    //-----------------
    // output stage
    //-----------------
    if (i < imgSize) {
    out[i * 3 + 0] = fmax(fmin(output.x, 1.0f), 0.0f); // r
    out[i * 3 + 1] = fmax(fmin(output.y, 1.0f), 0.0f); // g
    out[i * 3 + 2] = fmax(fmin(output.z, 1.0f), 0.0f); // b
    }
}