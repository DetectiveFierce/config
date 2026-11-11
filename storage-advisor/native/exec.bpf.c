#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

#ifndef TARGET_UID
#define TARGET_UID 1000
#endif

/* sched_process_exec tracepoint fields, checked against this kernel's BTF. */
struct exec_trace {
    __u64 common;
    __u32 filename_loc;
    __s32 pid;
    __s32 old_pid;
};

struct event {
    __u32 pid;
    __u8 kind;
    char exe[256];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 20);
} events SEC(".maps");

SEC("tp/sched/sched_process_exec")
int on_exec(struct exec_trace *ctx)
{
    __u32 uid = (__u32)bpf_get_current_uid_gid();
    if (uid != TARGET_UID)
        return 0;
    struct event *out = bpf_ringbuf_reserve(&events, sizeof(*out), 0);
    if (!out)
        return 0;
    out->pid = (__u32)(bpf_get_current_pid_tgid() >> 32);
    out->kind = 'E';
    __u32 offset = ctx->filename_loc & 0xffff;
    bpf_probe_read_kernel_str(out->exe, sizeof(out->exe), (void *)ctx + offset);
    bpf_ringbuf_submit(out, 0);
    return 0;
}

SEC("tp/sched/sched_process_exit")
int on_exit(void *ctx)
{
    __u32 uid = (__u32)bpf_get_current_uid_gid();
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    if (uid != TARGET_UID || (__u32)pid_tgid != (__u32)(pid_tgid >> 32))
        return 0;
    struct event *out = bpf_ringbuf_reserve(&events, sizeof(*out), 0);
    if (!out)
        return 0;
    out->pid = (__u32)(pid_tgid >> 32);
    out->kind = 'X';
    out->exe[0] = 0;
    bpf_ringbuf_submit(out, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
