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
                         const int maxSpp, const int matCount) {
  int i = get_global_id(0);
  float3 output = (float3)(0.0f);
  unsigned int seed0 = i % imgSize; /* x-coordinate of the pixel */
  unsigned int seed1 = i / imgSize;

  int matChunkSize = 6;
  int spp = 0;

  float epsilon = 0.00001f;
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

  //-----------------
  // Raytracing logic
  //-----------------
  while (spp < maxSpp) // each sample
  {
    ray R_cam = r;
    // first camera Ray
    spp++;
    float3 sampleOut = (float3)(1.0f);

    // fire cam ray
    hitInfo H_cam = rayTrace(R_cam, vertex_p, vertex_n, vertex_uv, face_data, triCount);
    material camMat = extractMaterial(mat, H_cam.mat);

    if (H_cam.bHit) 
    {
      sampleOut = camMat.color; // initialise with base color;
    }
    else 
    {
      sampleOut = (float3)(0.0f); // initialise with background
    }

    for (int j = 0; j < 2; j++) // max bounce limit
    {
        if (H_cam.bHit) 
        {
            // bounce Ray
            if (camMat.type != 0) 
            {
                // next ray setup
                float invPdfBounce;
                ray R_bounce;
                R_bounce.dir = rand_hemi_uniform(H_cam.n, &seed1, &seed0, &invPdfBounce);
                R_bounce.o = (R_cam.o + (normalize(R_cam.dir)*H_cam.k)) + (normalize(H_cam.n) * epsilon);
                //printVec( R_bounce.dir);
                // next ray shoot
                hitInfo H_bounce = rayTrace(R_bounce, vertex_p, vertex_n, vertex_uv,face_data, triCount);
                material bounceMat = extractMaterial(mat, H_bounce.mat);

                // next sampling calculation
                float att = invPdfBounce * dot(R_bounce.dir, normalize(H_cam.n)) * (1.0f / 3.14f);


                if (H_bounce.bHit) // hit something
                {
                    R_cam = R_bounce;
                    H_cam = H_bounce;
                    camMat = bounceMat;
                    sampleOut = sampleOut*bounceMat.color * (att);
                    if (bounceMat.type != 0) 
                    {
                        if (j == 1) 
                        {
                            sampleOut = sampleOut*(float3)(0.0f);
                            break;
                        }
                    } 
                    else 
                    {
                        sampleOut = sampleOut*10.0f;
                        break;
                    }
                } 
                else // lost in background
                {
                    sampleOut = sampleOut*(float3)(0.1f);
                    break;
                }
            }
            else
            {
                break;
            }
        }
        else
        {
            break;
        }
    }

    output = output + sampleOut;

    /*         //russian roulette
             while(rand(seed0,seed1) < 1.0f/sampleOut.length)
            {

                hitInfo H =
       rayTrace(r,vertex_p,vertex_n,vertex_uv,face_data,triCount); if (H.bHit)
                {
                    //(1-(H.k/2.0f))
                    output = (float3)(mat[H.mat*matChunkSize +
       1],mat[H.mat*matChunkSize + 2],mat[H.mat*matChunkSize +
       3])*(1.0f-H.k/5.0f);
                }
            }  */
  }
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
