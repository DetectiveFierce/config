#include <bpf/libbpf.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct event {
    uint32_t pid;
    uint8_t kind;
    char exe[256];
};

static volatile sig_atomic_t running = 1;

static void stop(int signal_number) { (void)signal_number; running = 0; }

static int emit(void *context, void *data, size_t size)
{
    (void)context;
    if (size < sizeof(struct event)) return 0;
    const struct event *item = data;
    if (item->kind == 'X') {
        printf("X\t%u\n", item->pid);
        return 0;
    }
    if (item->kind != 'E') return 0;
    printf("E\t%u\t", item->pid);
    for (size_t i = 0; i < sizeof(item->exe) && item->exe[i]; i++)
        printf("%02x", (unsigned char)item->exe[i]);
    putchar('\n');
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: exec_collector PATH_TO_BPF_OBJECT\n");
        return 2;
    }
    setvbuf(stdout, NULL, _IOLBF, 0);
    signal(SIGTERM, stop);
    signal(SIGINT, stop);
    struct bpf_object *obj = bpf_object__open_file(argv[1], NULL);
    if (!obj || libbpf_get_error(obj)) return 3;
    if (bpf_object__load(obj)) {
        fprintf(stderr, "cannot load BPF program\n");
        bpf_object__close(obj);
        return 4;
    }
    struct bpf_program *program;
    struct bpf_link *links[2] = {0};
    int i = 0;
    bpf_object__for_each_program(program, obj) {
        const char *name = bpf_program__name(program);
        const char *event = !strcmp(name, "on_exec") ? "sched_process_exec" : "sched_process_exit";
        links[i++] = bpf_program__attach_tracepoint(program, "sched", event);
        if (i >= 2) break;
    }
    if (!links[0] || !links[1] || libbpf_get_error(links[0]) || libbpf_get_error(links[1])) {
        fprintf(stderr, "cannot attach process tracepoints\n");
        bpf_object__close(obj);
        return 5;
    }
    struct bpf_map *map = bpf_object__find_map_by_name(obj, "events");
    struct ring_buffer *ring = ring_buffer__new(bpf_map__fd(map), emit, NULL, NULL);
    if (!ring) {
        fprintf(stderr, "cannot open event ring\n");
        return 6;
    }
    while (running && ring_buffer__poll(ring, 500) >= 0) { }
    ring_buffer__free(ring);
    bpf_link__destroy(links[0]);
    bpf_link__destroy(links[1]);
    bpf_object__close(obj);
    return 0;
}
