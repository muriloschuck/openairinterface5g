#include <pthread.h>
int x;
static void *f(void *a) { for (int i = 0; i < 100000; i++) x++; return a; }
int main(void) { pthread_t t1, t2; pthread_create(&t1, 0, f, 0); pthread_create(&t2, 0, f, 0);
                 pthread_join(t1, 0); pthread_join(t2, 0); return 0; }
