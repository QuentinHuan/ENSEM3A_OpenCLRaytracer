#include "stack.cl"

//--------------------
//  data structures
//--------------------
typedef struct vertex
{
    float2 uv;
    float3 n, p;
} vertex;

typedef struct tri
{
    int m;
    vertex a, b, c;
} tri;

typedef struct ray
{
    float3 dir, o;
} ray;

typedef struct hitInfo
{
    float3 n;
    float2 uv;
    float k;
    int mat;
    bool bHit;
} hitInfo;

typedef struct material
{
    int type;
    float3 color;
    float roughness;
    float ior;
} material;

typedef struct box
{
    float3 min, max, center;
	float3 bounds[2];
} box;


//-----------------------------------------------
// quaternion implementation for vector rotation
//-----------------------------------------------

float4 quaternion_mult(float4 q, float4 p)
{
    return (float4)(q.x * p.x - dot(q.yzw, p.yzw), q.yzw * p.x + p.yzw * q.x + cross(q.yzw, p.yzw));
}
//rotate a vector on axis "axis" by angle "angle" (rad)
static float3 rotateVec(float angle, float3 axis, float3 vector)
{
    //using quaternions
    float4 q = (float4)(cos(angle *0.5f), normalize(axis) * sin(angle *0.5f));
    float4 V = (float4)(0, vector);

    float4 qinv = normalize((float4)(q.x, q.yzw*(-1.0f)) * (q.x*q.x + dot(q.yzw, q.yzw)));

    return (quaternion_mult(quaternion_mult(q,V), qinv)).yzw;
}

//--------------
// IBL sampling
//--------------

//pick a pixel in spherical space
float2 SampleSphericalMap(float3 direction) {
    direction=rotateVec(90*(3.14f/180.0f),(float3)(1,0,0),direction);
    direction=rotateVec(90*(3.14f/180.0f),(float3)(0,1,0),direction);
    float2 invAtan = (float2)(0.1591f, 0.3183f);
    float2 uv = (float2)(atan2(direction.z, direction.x), asin(direction.y));
    uv = uv * invAtan;
    uv = uv + 0.5f;
    return uv;
}

//sample environnement Image
// need rework: hardcoded image size
float3 sampleIBL(float3 dir,sampler_t sampler, __read_only image2d_t IBL)
{
    float2 uv = SampleSphericalMap(dir);
    float4 pix = read_imagef(IBL, sampler, (int2)(uv.x*get_image_width(IBL),uv.y*get_image_height(IBL)));

    return 1.0f*pix.xyz;
}

//----------------------------
// BRDF space to global space
//----------------------------
float3 localToGlobal(float3 localV, float3 dir)
{
    float3 worldV;
    float colinear = fabs(dot(normalize(dir),(float3)(0.0f, 0.0f, 1.0f)));
    if (colinear == 1.0f)
    {
        worldV = localV*dir.z;
    }
    else
    {
        float3 axis = normalize(cross((float3)(0.0f, 0.0f, 1.0f), dir));
        float rotAngle = acos(dot(dir, (float3)(0, 0, 1.0f)));
        worldV = rotateVec(rotAngle, axis, localV);
    }
    return worldV;
}

//-----------------------
// triangle intersection
//-----------------------
//test intersections between Ray 'r' and Triangle 'T'
//return hitInfo structure
hitInfo intersect(tri T, ray r)
{
    const float EPSILON = 0.0000001;
    float maxDist = 1000.0f;

    hitInfo output;
    output.bHit = false;
    output.k = maxDist;
    output.mat = 0;

    float3 edge1, edge2, h, s, q;
    float a, f, u, v;
    edge1 = T.b.p - T.a.p;
    edge2 = T.c.p - T.a.p;
    h = cross(r.dir, edge2);
    a = dot(edge1, h);

    if (a > -EPSILON && a < EPSILON)
        return output; // This ray is parallel to this triangle.

    f = 1.0 / a;
    s = r.o - T.a.p;
    u = f * dot(s, h);
    if (u < 0.0 || u > 1.0) // outside of triangle
        return output;

    q = cross(s, edge1);
    v = f * dot(r.dir, q);
    if (v < 0.0 || u + v > 1.0) // outside of triangle
        return output;
    // At this stage we can compute t to find out where the intersection point is on the line.
    float k = f * dot(edge2, q);
    if (k > EPSILON) // ray intersection
    {
        output.n = T.a.n;   //TODO --> normal interpolation
        output.uv = T.a.uv; //TODO --> uv interpolation
        output.k = k;
        output.mat = T.m; //TODO --> find material from 3 Vertex
        output.bHit = true;
        return output;
    }
    else // This means that there is a line intersection but not a ray intersection.
        return output;
}

//---------------
// BVH traversal
//---------------

// ray/box intersection
bool intersectBox(ray r, box b)
{ 
    float tx1 = (b.min.x - r.o.x)/r.dir.x;
    float tx2 = (b.max.x - r.o.x)/r.dir.x;

    float tmin = fmin(tx1, tx2);
    float tmax = fmax(tx1, tx2);

    float ty1 = (b.min.y - r.o.y)/r.dir.y;
    float ty2 = (b.max.y - r.o.y)/r.dir.y;

    tmin = fmax(tmin, fmin(ty1, ty2));
    tmax = fmin(tmax, fmax(ty1, ty2));


    float tz1 = (b.min.z - r.o.z)/r.dir.z;
    float tz2 = (b.max.z - r.o.z)/r.dir.z;

    tmin = fmax(tmin, fmin(tz1, tz2));
    tmax = fmin(tmax, fmax(tz1, tz2));

    return(tmax >= tmin);

} 

// node intersection : intersect with node box
bool interNode(ray r, __constant float *BVH, int curr)
{
    box b; 
    b.min = (float3)(BVH[9*curr + 2],BVH[9*curr + 3],BVH[9*curr + 4]);
    b.max = (float3)(BVH[9*curr + 5],BVH[9*curr + 6],BVH[9*curr +7]);
    return intersectBox(r,b);
}

//helper function:
//pack triangle data in a convenient data structure
tri makeTri(int k,__constant float *vertex_p,__constant float *vertex_n,__constant float *vertex_uv, __constant int *face_data,const int triCount)
{
        tri T;
        T.m = (int)face_data[k*10];//material

        vertex V[3];
        for (int j = 0; j < 3; j++) //iterate through 3 vertex
        {
            vertex v;
            int uvId = (int)face_data[k*10 + j + 1];
            
            int nId = (int)face_data[k*10 + j + 4];
            int pId = (int)face_data[k*10 + j + 7];

            v.uv = (float2)(vertex_uv[uvId*2 + 0], vertex_uv[uvId*2 + 1]);
            v.n = (float3)(vertex_n[nId*3 + 0], vertex_n[nId*3 + 1], vertex_n[nId*3 + 2]);
            v.p = (float3)(vertex_p[pId*3 + 0], vertex_p[pId*3 + 1], vertex_p[pId*3 + 2]);

            V[j] = v;
        }

        T.a = V[0];
        T.b = V[1];
        T.c = V[2];
        return T;
}

//---------------------
//      rayTrace
//---------------------
//--> test all triangle intersections along ray 'r'
hitInfo rayTrace(ray r,__constant float *vertex_p,__constant float *vertex_n,__constant float *vertex_uv, __constant int *face_data,const int triCount,__constant float *BVH)
{
    hitInfo H;
    H.n = (float3)(0,0,0);
    H.uv = (float2)(0,0);
    H.k = 1000.0f;
    H.mat = 0;
    H.bHit = false;

    hitInfo HTemp;
    //BVH tree traversal:
    int curr = 0;
    int m =0;
    struct Stack S;
    S.capacity = 20;
    S.top = -1;
    push(&S,0);
        //pre-order tree traversal (non recursive)
        while(!isEmpty(&S))
        {
            curr = (int)(pop(&S));
            if(interNode(r,BVH,(int)curr))
            {
                if((int)(BVH[9*curr+8]) != -1)//leaf node
                {
                    //traitement
                    tri T = makeTri((int)(BVH[9*curr+8]),vertex_p,vertex_n,vertex_uv,face_data,triCount);
                    HTemp = intersect(T, r);
                   
                    if(HTemp.bHit && HTemp.k < H.k && HTemp.k > 0.0001f)
                    {
                        H=HTemp;
                    }
                }
                //left
                if ((int)(BVH[9*curr]) != -1)
                {
                    push(&S,(int)(BVH[9*curr]));
                }
                //right
                if ((int)(BVH[9*curr+1]) != -1)
                {
                    push(&S,(int)(BVH[9*curr+1]));
                }
            }

        }

    if(H.k <= 0.0001f)
    {
        H.bHit = false;
        H.k = 0.0f;
    }
    return H;
}

///////////////////////////////
//------------
//Random
//------------
static float rand(unsigned int *seed0, unsigned int *seed1) {

	/* hash the seeds using bitwise AND operations and bitshifts */
	*seed0 = 36969 * ((*seed1) & 65535) + ((*seed1) >> 16);  
	*seed1 = 18000 * ((*seed0) & 65535) + ((*seed0) >> 16);

	unsigned int ires = ((*seed0) << 16) + (*seed1);

	/* use union struct to convert int to float */
	union {
		float f;
		unsigned int ui;
	} res;

	res.ui = (ires & 0x007fffff) | 0x40000000;  /* bitwise AND, bitwise OR */
	return (res.f - 2.0f) / 2.0f;
}

//hemisphere sampling cosine distribution
static float3 rand_hemi_cosine(float3 dir, unsigned int *seed0, unsigned int *seed1, float *invPdf)
{
    //lambert cosine weighted
    float u = rand(seed0,seed1);				  //[0,1]
    float theta = rand(seed0,seed1) * 2.0f * 3.14f; //[0,2pi]

    const float r = sqrt(u);
    const float x = r * cos(theta);
    const float y = r * sin(theta);
    float3 localV = (float3)(x, y, sqrt(fmax(0.0f, 1.0f - u)));
    float3 l;

    float colinear = fabs(dot(normalize(dir),(float3)(0.0f, 0.0f, 1.0f)));
    if (colinear == 1.0f)
    {
        //printf("norm");
        l = localV*dir.z;
    }
    else
    {
        float3 axis = cross((float3)(0, 0, 1), dir);
        float rotAngle = acos(dot(dir, (float3)(0, 0, 1)));
        l = normalize(rotateVec(rotAngle, axis, localV));
    }
    *invPdf = 3.14f / (fmax(dot(l, dir),0.0f));
    return l;
}

//hemisphere sampling uniform distribution
 static float3 rand_hemi_uniform(float3 dir, unsigned int *seed0, unsigned int *seed1, float *invPdf)
{
    float phi = 2.0f*3.14f*(rand(seed0,seed1));
    float theta = acos(1.0f-(rand(seed0,seed1)));
    float3 localV = (float3)(cos(phi)*sin(theta), sin(theta)*sin(phi),cos(theta));
    
    float3 worldV;
    float colinear = fabs(dot(normalize(dir),(float3)(0.0f, 0.0f, 1.0f)));
    if (colinear == 1.0f)
    {
        //printf("norm");
        worldV = localV*dir.z;
    }
    else
    {
        float3 axis = normalize(cross((float3)(0.0f, 0.0f, 1.0f), dir));
        float rotAngle = acos(dot(dir, (float3)(0, 0, 1.0f)));
        //worldV = dir;
        worldV = rotateVec(rotAngle, axis, localV);
        //printf("x %f y %f z %f",worldV.x,worldV.y,worldV.z);
    }

    *invPdf = 2.0f*3.14f;
    return worldV;
} 

//hemisphere sampling GGX distribution
static float3 rand_sample_GGX(material m, float3 v, float3 n, unsigned int *seed0, unsigned int *seed1, float *invPdf)
{
    //GGX
    float alphaSqr = (pown(m.roughness,2));
    //float alphaSqr = 10.0f;
    float u = rand(seed0,seed1);				//[0,1]
    float phi = rand(seed0,seed1) * 1.0f * 3.14f; //[0,2pi]
    float theta = acos(sqrt((1.0f - u)/((alphaSqr - 1.0f) * u + 1.0f)));
    float st = sin(theta);
    float3 localV = (float3)(st * cos(phi), st * sin(phi), cos(theta));

    float3 worldV = localToGlobal(localV,n);

    float3 l = worldV * 2.0f * dot(v, worldV) - v;
    float D = alphaSqr /
                (3.14f * pown(pown(fmax(dot(n, worldV), 0.0f), 2) * (alphaSqr - 1.0f) + 1.0f, 2));
    *invPdf = (1.0f * fabs(dot(worldV, v))) / (D * dot(worldV, n));
    return worldV;
} 

//hemisphere sampling Glass distribution
//simply return the incoming ray 
static float3 rand_sample_Glass(float3 v, float *invPdf)
{
    *invPdf = 1.0f;
    return v;
} 


float Tri_area(tri t)
{
	float3 u = t.a.p - t.b.p, v = t.a.p - t.c.p;
	return length(cross(u, v))/2.0;
}

float3 uniformRndInTriangle(tri t, unsigned int *seed0, unsigned int *seed1)
{
	float u1 = rand(seed0,seed1);
	float u2 = rand(seed0,seed1);

	float s = sqrt(u1);
	float x = 1.0f - s;
	float y = u2 * s;
	float3 U = t.b.p - t.a.p;
	float3 V = t.c.p - t.a.p;
	float3 v = t.a.p + (U * x + V * y);
	return v;
}

//direct light sampling
static float3 sampleLight(float3 hitPos,__constant float *vertex_p,__constant float *vertex_n,__constant float *vertex_uv,
 __constant int *face_data,const int triCount,__constant int *light_data,const int lightCount,unsigned int *seed0,
  unsigned int *seed1, float *invPDF,__global float *envData)
{
    float3 n;
	if (lightCount>0)
	{
		int r = convert_int_rte(rand(seed0,seed1)*(lightCount+1));
        if(r == lightCount)//sample sun
        {
            n = (float3)(1);
            n = rotateVec(envData[0]*(3.14f/180.0f),(float3)(1,0,0),n); // x angle
            n = rotateVec(envData[1]*(3.14f/180.0f),(float3)(0,1,0),n); // y angle
            n = rotateVec(envData[2]*(3.14f/180.0f),(float3)(0,0,1),n); // z angle
            *invPDF = lightCount+1;
        }
        else
        {
            tri t = makeTri(light_data[0],vertex_p,vertex_n,vertex_uv,face_data,triCount);
            n = (uniformRndInTriangle(t,seed1,seed0) - hitPos);
            n = normalize(n);
            *invPDF = (lightCount+1)*envData[4] * (fmax(dot(t.a.n, -n), 0.0f)) * (Tri_area(t) / pown(length(n),2));
        }
		
		return n;
	}
	else
    {
		    n = (float3)(1);
            n = rotateVec(envData[0]*(3.14f/180.0f),(float3)(1,0,0),n); // x angle
            n = rotateVec(envData[1]*(3.14f/180.0f),(float3)(0,1,0),n); // y angle
            n = rotateVec(envData[2]*(3.14f/180.0f),(float3)(0,0,1),n); // z angle
            *invPDF = (lightCount+1)*envData[3];
            return n;
    }
}


//------------
//    BRDF
//------------
//GGX BRDF
float3 BRDF_GGX(material m, float3 v, float3 l, float3 n)
{
    //----------------------||
    //        vectors
    //----------------------||
    float3 h = normalize(l + v);
    //----------------------||
    //  Specular Component
    //----------------------||
    float alphaSqr = (pown(m.roughness,2));
    float D = alphaSqr /
                (3.14f * pown(pown(fmax(dot(n, h), 0.0f), 2) * (alphaSqr - 1.0f) + 1.0f, 2));

    float NdotV = fmax(dot(n, v), 0.0f);
    float k = m.roughness * sqrt(2.0f / 3.14f);
    float G1 = NdotV / (NdotV * (1.0f - k) + k);

    float NdotL = fmax(dot(n, l), 0.0f);
    float G2 = NdotL / (NdotL * (1.0f - k) + k);
    float G = G1 * G2;
    float F0 = 0.04f;
    float F =
        F0 + (1 - F0) * pown(1.0f - fmax(dot(h, v), 0.0f), 5);

    float specular =(F * G * D) * (1.0f / fmax(4.0f * fmax(dot(v, n), 0.0f) * fmax(dot(l, n), 0.0f), 0.001f));

    //----------------------||
    //   Diffuse Component
    //----------------------||

    float3 kd = (float3)(1.0f) - F;
    kd = kd * (1.0f - 0.5f);

    float NdotOmega = fmax(dot(n, l), 0.0f);
    float3 diffuse = kd * m.color / 3.14f;

    float3 result = (diffuse + specular);

    return result;
}

//Lambert BRDF
float3 BRDF_Lambert(material m)
{
    return (m.color * (1.0f / 3.14f));
}

//Glass BRDF
float3 BRDF_Glass(material m)
{
    return (m.color);
}