#include "stack.cl"

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


//------------
//rotation
//------------
float4 quaternion_mult(float4 q, float4 p)
{
    return (float4)(q.x * p.x - dot(q.yzw, p.yzw), q.yzw * p.x + p.yzw * q.x + cross(q.yzw, p.yzw));
}

static float3 rotateVec(float angle, float3 axis, float3 vector)
{
    //using quaternions
    float4 q = (float4)(cos(angle *0.5f), normalize(axis) * sin(angle *0.5f));
    float4 V = (float4)(0, vector);

    float4 qinv = normalize((float4)(q.x, q.yzw*(-1.0f)) * (q.x*q.x + dot(q.yzw, q.yzw)));

    return (quaternion_mult(quaternion_mult(q,V), qinv)).yzw;
}

//IBL sampling

float2 SampleSphericalMap(float3 direction) {
    direction=rotateVec(90*(3.14f/180.0f),(float3)(1,0,0),direction);
    direction=rotateVec(90*(3.14f/180.0f),(float3)(0,1,0),direction);
    float2 invAtan = (float2)(0.1591f, 0.3183f);
    float2 uv = (float2)(atan2(direction.z, direction.x), asin(direction.y));
    uv = uv * invAtan;
    uv = uv + 0.5f;
    return uv;
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


//---------------------
//      intersect
//---------------------
//--> test intersections between Ray 'r' and Triangle 'T'
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
bool intersectBox(ray r, box b)
{ 
    float tx1 = (b.min.x - r.o.x)/r.dir.x;
    float tx2 = (b.max.x - r.o.x)/r.dir.x;

    float tmin = fmin(tx1, tx2);
    float tmax = fmax(tx1, tx2);

    return tmax >= tmin;

    float ty1 = (b.min.y - r.o.y)/r.dir.y;
    float ty2 = (b.max.y - r.o.y)/r.dir.y;

    tmin = fmax(tmin, fmin(ty1, ty2));
    tmax = fmin(tmax, fmax(ty1, ty2));

    float tz1 = (b.min.z - r.o.z)/r.dir.z;
    float tz2 = (b.max.z - r.o.z)/r.dir.z;

    tmin = fmax(tmin, fmin(tz1, tz2));
    tmax = fmin(tmax, fmax(tz1, tz2));


} 

bool interNode(ray r, __constant float *BVH, int curr)
{
    box b; 
    b.min = (float3)(BVH[9*curr + 2],BVH[9*curr + 3],BVH[9*curr + 4]);
    b.max = (float3)(BVH[9*curr + 5],BVH[9*curr + 6],BVH[9*curr +7]);
    return intersectBox(r,b);
}

tri makeTri(int index,__constant float *vertex_p,__constant float *vertex_n,__constant float *vertex_uv, __constant int *face_data,const int triCount)
{
        int k = index;
        tri T;
        T.m = (int)face_data[k*10];//material
        vertex V[3];
        int c = 0;
        for (int j = 0; j < 3; j++) //iterate through 3 vertex
        {
            vertex v;
            int uvId = (int)face_data[k*10 + j + 1];
            
            int nId = (int)face_data[k*10 + j + 4];
            int pId = (int)face_data[k*10 + j + 7];

            v.uv = (float2)(vertex_uv[uvId*2 + 0], vertex_uv[uvId*2 + 1]);
            v.n = (float3)(vertex_n[nId*3 + 0], vertex_n[nId*3 + 1], vertex_n[nId*3 + 2]);
            v.p = (float3)(vertex_p[pId*3 + 0], vertex_p[pId*3 + 1], vertex_p[pId*3 + 2]);

            V[c] = v;
            c++;
        }
        T.a = V[0];T.b = V[1];T.c = V[2];
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
    //printf("m=%d",m);
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

static float3 rand_sample_Glass(float3 v, float *invPdf)
{
    *invPdf = 1.0f;
    return v;
} 

//------------
//    BRDF
//------------
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
		float3 result = ((float3)(1.0f, 1.0f, 1.0f) * specular);

		return result;
	}

    float3 BRDF_Lambert(material m)
	{
		return (m.color * (1.0f / 3.14f));
	}

    float3 BRDF_Glass(material m)
	{
		return (m.color);
	}