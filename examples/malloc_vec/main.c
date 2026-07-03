#include <stdio.h>
#include <stdlib.h>

int *make_sequence(int len) {
    int *values = malloc(sizeof(int) * len);
    for (int i = 0; i < len; i++) {
        values[i] = i;
    }
    return values;
}

int main(void) {
    int len = 5;
    int *values = make_sequence(len);
    for (int i = 0; i < len; i++) {
        printf(i + 1 == len ? "%d\n" : "%d ", values[i]);
    }
    free(values);
    return 0;
}
