__kernel void ImgProcessing(__global float *in, __global float *out, const int N)
{
    int i = get_global_id(0);
    if(i < N)
    {
        float p = min(in[i],1.0f);//max 1.0
        out[i] = powr(p,2.2f);//gamma correction
    }

}