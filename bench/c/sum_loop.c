/* Null benchmark baseline: 1..n integer sum, the scalar-loop workload. */
#include <stdio.h>
#include <stdint.h>

int main(void) {
    volatile int64_t n = 100000000;
    int64_t total = 0;
    for (int64_t i = 1; i <= n; i++) {
        total += i;
    }
    printf("%lld\n", (long long)total);
    return 0;
}
