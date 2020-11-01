__kernel void kernel3(__global float *a, __global float *b, __global float *c, const unsigned int N)
{
    int k, j;
    int i = get_global_id(0);
    float A_Row_private[1024];
    int l = get_local_id(0);

    for (k = 0; k < N; k++)
    {
        A_Row_private[k] = a[i * N + k];
    }

    float tmp;
    if (i < N)
    {
        for (j = 0; j < N; j++)
        {
            tmp = 0.0f;
            for (k = 0; k < N; k++)
                tmp += A_Row_private[k] * b[k * N + j];
            c[i * N + j] = tmp;
        }
    }
}
