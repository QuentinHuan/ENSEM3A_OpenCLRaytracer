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

void printVec(float3 v) {
  printf("x %f y %f z %f", v.x, v.y, v.z);
  return;
}
//------------------------------------
// raytracing kernel
// data and mat as defined in 'scene' class member 'vertexData' and
// 'materialData' cam --> the camera, [x,y,z,dx,dy,dz] out --> the output color
// []
__kernel void Raytracing(__global float *out, __constant float *vertex_p,
                         __constant float *vertex_n,
                         __constant float *vertex_uv, __constant int *face_data,
                         __global float *mat, __global float *cam,
                         const int triCount, const int imgSize,
                         const int maxSpp, const int maxBounce) {
    //--------------
    //initialise
    //--------------
  int i = get_global_id(0);
  float3 output = (float3)(0.0f);
  unsigned int seed0 = i % imgSize; /* x-coordinate of the pixel */
  unsigned int seed1 = i / imgSize;

  int matChunkSize = 6;
  int spp = 0;

  float epsilon = 0.00001f;

  float3 backgroundColor = (float3)(0.1f);
  //-----------------
  // Ray construction
  //-----------------

  //---> NEED REWORK <---//

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

  // fire cam ray
  hitInfo H_cam_cache = rayTrace(r, vertex_p, vertex_n, vertex_uv, face_data, triCount);
  material camMat_cache = extractMaterial(mat, H_cam_cache.mat);
  //-----------------
  // Raytracing logic
  //-----------------
  while (spp < maxSpp) // for each sample
  {
    spp++;
    // load first ray and result from cache
    ray R_cam = r;
    hitInfo H_cam = H_cam_cache;
    material camMat = camMat_cache;

    //sample out initialisation
    float3 sampleOut = (float3)(1.0f);
    if (H_cam.bHit)sampleOut = camMat.color; // initialise with base color;
    else sampleOut = backgroundColor; // initialise with background

    // camRay is the previous ray
    // bounce ray the new ray that bounce of the surface
    for (int j = 0; j <= maxBounce; j++) // max bounce limit
    {
        if (H_cam.bHit) 
        {
            // bounce Ray
            if (camMat.type != 0) 
            {
                // next ray setup
                float invPdfBounce;
                ray R_bounce;

                //sampling method selection depending on current surface's material
                switch(camMat.type)
                {
                    case 0://emissive
                        R_bounce.dir = rand_hemi_uniform(H_cam.n, &seed1, &seed0, &invPdfBounce);
                        break;
                    case 1://diffuse
                        R_bounce.dir = rand_hemi_cosine(H_cam.n, &seed1, &seed0, &invPdfBounce);
                        break;
                    case 2://Glossy GGX
                        R_bounce.dir = rand_hemi_uniform(H_cam.n, &seed1, &seed0, &invPdfBounce);
                        break;
                    case 3://Glass
                        R_bounce.dir = rand_hemi_uniform(H_cam.n, &seed1, &seed0, &invPdfBounce);
                        break;
                }

                R_bounce.o = (R_cam.o + (normalize(R_cam.dir) * H_cam.k)) + (normalize(H_cam.n) * epsilon);

                // next ray shoot
                hitInfo H_bounce = rayTrace(R_bounce, vertex_p, vertex_n, vertex_uv, face_data, triCount);
                material bounceMat = extractMaterial(mat, H_bounce.mat);

                // attenuation calculation
                float att = invPdfBounce * dot(R_bounce.dir, normalize(H_cam.n)) * (1.0f / 3.14f);

                if (H_bounce.bHit) // hit something solid
                {
                    //swap bounce and cam ray
                    R_cam = R_bounce;
                    H_cam = H_bounce;
                    camMat = bounceMat;
                    //add bounce contribution
                    sampleOut = sampleOut * bounceMat.color * (att);
                    if (bounceMat.type != 0) 
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
                        sampleOut = sampleOut * 10.0f;
                        break;
                    }
                } 
                else // lost in background
                {
                    sampleOut = sampleOut*backgroundColor;
                    break;
                }
            } 
            else break;
        } 
        else break;
    }
    output = output + sampleOut;
  }
  //mean
  output = output * (1.0f / (float)(maxSpp));

  //-----------------
  // output stage
  //-----------------
  if (i < imgSize) {

    out[i * 3 + 0] = fmax(fmin(output.x, 1.0f), 0.0f); // r
    out[i * 3 + 1] = fmax(fmin(output.y, 1.0f), 0.0f); // g
    out[i * 3 + 2] = fmax(fmin(output.z, 1.0f), 0.0f); // b
  }
}
