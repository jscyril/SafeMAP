#include <stdio.h>

int has_inline_asm(int value) {
    __asm__ volatile ("nop");
    return value;
}

int main(void) {
    printf("%d\n", has_inline_asm(4));
    return 0;
}
