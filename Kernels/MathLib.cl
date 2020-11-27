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

    float4 qinv = (float4)(q.x, q.yzw*(-1.0f)) * (q.x*q.x + dot(q.yzw, q.yzw));

    return (quaternion_mult(quaternion_mult(q,V), qinv)).yzw;
}

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
		float3 axis = cross((float3)(0, 0, 1), dir);
		if (dir.x == 0.0f && dir.y == 0.0f && dir.z == 0.0f)
        {
            l = normalize(localV);
        }
		else
		{
            float rotAngle = acos(dot(dir, (float3)(0, 0, 1)));
            l = normalize(rotateVec(rotAngle, axis, localV));
		}
        *invPdf = 3.14f / (fmax(dot(l, dir),0.0f));
        return l;
	}

 static float3 rand_hemi_uniform(float3 dir, unsigned int *seed0, unsigned int *seed1, float *invPdf)
{
    float theta0=2.0f*3.14f*(rand(seed0,seed1));
    float theta1 = acos(1.0f-2.0f*rand(seed0,seed1));
    float3 localV = (float3)(sin(theta0)*sin(theta1), sin(theta0)*cos(theta1),sin(theta1));
    
    float3 worldV;
    float3 axis = cross((float3)(0.0f, 0.0f, 1.0f), dir);
    if (dir.x == 0.0f && dir.y == 0.0f && dir.z == 0.0f)
    {
        worldV = localV;
    }
    else
    {
        float rotAngle = acos(dot(dir, (float3)(0, 0, 1)));
        worldV = rotateVec(rotAngle, axis, localV);
        //printf("x %f y %f z %f",worldV.x,worldV.y,worldV.z);
    }

    *invPdf = 2*3.14;
    return normalize(worldV);
} 


//---------------------
//      intersect
//---------------------

//--> test intersections between Ray 'r' and Triangle 'T'
hitInfo intersect(tri T, ray r)
{
    const float EPSILON = 0.0000001;
    const float maxDist = 1000.0f;

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
    if (u < 0.0 || u > 1.0)
        return output;

    q = cross(s, edge1);
    v = f * dot(r.dir, q);
    if (v < 0.0 || u + v > 1.0)
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
//---------------------
//      rayTrace
//---------------------

//--> test all triangle intersections along ray 'r'
hitInfo rayTrace(ray r,__constant float *vertex_p,__constant float *vertex_n,__constant float *vertex_uv, __constant int *face_data,const int triCount)
{
    hitInfo H;
    hitInfo HTemp;
    for (int k = 0; k < triCount; k++)
    {
        //build triangle
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
        
        if(k==0) H = intersect(T, r);
        else HTemp = intersect(T, r);
        
        if(HTemp.bHit && HTemp.k < H.k && HTemp.k > 0.0f)
        {
            H=HTemp;
        }
    } 

    if(H.k < 0.0f)
    {
        H.bHit = false;
        H.k = 0.0f;
    }
    return H;
}