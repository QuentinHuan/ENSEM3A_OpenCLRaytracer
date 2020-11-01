__kernel void kernel2(__global float *a, __global float *b, __global float *c, const unsigned int N)
{
    int k, j;
    int i = get_global_id(0);
    float tmp;
    if (i < N) {
        for (j = 0; j < N; j++) {
            tmp = 0.0f;
            for (k = 0; k < N; k++)
                tmp += a[i*N+k] * b[k*N+j];
            c[i*N+j] = tmp;
        }
    }
}
