#include <stdio.h>
#include <string.h>

size_t byte_len(const char *text) {
    return strlen(text);
}

int main(void) {
    printf("%zu\n", byte_len("hello"));
    return 0;
}
