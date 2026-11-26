/* Null benchmark baseline: sum of even squares, 1..n, fused single pass. */
#include <stdio.h>
#include <stdint.h>

int main(void) {
    volatile int64_t n = 20000000;
    int64_t total = 0;
    for (int64_t x = 1; x <= n; x++) {
        if (x % 2 == 0) {
            total += x * x;
        }
    }
    printf("%lld\n", (long long)total);
    return 0;
}
