#include <stdio.h>
#include <string.h>

int short_name_len(const char *text) {
    return strlen(text);
}

size_t title_len(const char *text) {
    return strlen(text);
}

long label_len(const char *text) {
    return strlen(text);
}

int main(void) {
    printf("%d %zu %ld\n", short_name_len("abc"), title_len("hello"), label_len("safe"));
    return 0;
}
