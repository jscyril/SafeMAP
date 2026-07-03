#include <stdio.h>
#include <stdlib.h>

int *make_owned(int value) {
    int *out = malloc(sizeof(int));
    *out = value;
    return out;
}

int *make_constant(void) {
    int *out = malloc(sizeof(int));
    *out = 42;
    return out;
}

int *make_sequence(int len) {
    int *values = malloc(sizeof(int) * len);
    for (int i = 0; i < len; i++) {
        values[i] = i;
    }
    return values;
}

int main(void) {
    int *owned = make_owned(7);
    int *constant = make_constant();
    int *sequence = make_sequence(3);
    printf("%d %d %d %d %d\n", *owned, *constant, sequence[0], sequence[1], sequence[2]);
    free(owned);
    free(constant);
    free(sequence);
    return 0;
}
