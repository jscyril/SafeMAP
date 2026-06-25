#include <stdio.h>
#include <stdlib.h>

int *make_value(int x) {
    int *p = malloc(sizeof(int));
    if (p == NULL) return NULL;
    *p = x;
    return p;
}

int main(void) {
    int *value = make_value(9);
    if (value == NULL) return 1;
    printf("%d\n", *value);
    free(value);
    return 0;
}

