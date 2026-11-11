CC ?= cc
CLANG ?= clang
TARGET_UID ?= 1000

all: build/exec.bpf.o build/exec_collector

build:
	mkdir -p build

build/exec.bpf.o: exec.bpf.c | build
	$(CLANG) -O2 -g -target bpf -D__TARGET_ARCH_x86 -DTARGET_UID=$(TARGET_UID) -c $< -o $@

build/exec_collector: exec_collector.c | build
	$(CC) -O2 -Wall -Wextra $< -lbpf -lelf -lz -o $@

clean:
	rm -rf build
