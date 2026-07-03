#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int apply(int (*op)(int, int), int a, int b) {
    return (*op)(a, b);
}

int main(void) {
    printf("%d\n", apply(add, 2, 3));
    return 0;
}
