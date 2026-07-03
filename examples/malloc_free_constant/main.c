#include <stdio.h>
#include <stdlib.h>

int *make_answer(void) {
    int *out = malloc(sizeof(int));
    *out = 42;
    return out;
}

int main(void) {
    int *out = make_answer();
    printf("%d\n", *out);
    free(out);
    return 0;
}
