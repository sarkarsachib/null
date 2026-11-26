/* Null benchmark baseline: element-wise a[i]*3+b[i] over 8M i64 elements. */
#include <stdio.h>
#include <stdint.h>

#define N 8000000

int main(void) {
    static int64_t a[N], b[N];
    for (int64_t i = 0; i < N; i++) {
        a[i] = i;
        b[i] = i * 2;
    }
    int64_t total = 0;
    for (int64_t i = 0; i < N; i++) {
        total += a[i] * 3 + b[i];
    }
    printf("%lld\n", (long long)total);
    return 0;
}
