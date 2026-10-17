# Pinned C2Rust baseline environment.
# C2Rust 0.22.1 built against LLVM/Clang 14 on Ubuntu 22.04 (glibc 2.35), the
# platform C2Rust is tested on. Host glibc releases newer than ~2.40 expose
# header constructs that crash the LLVM 14 AST exporter, so the baseline runs
# here instead of on the host.
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential ca-certificates cmake curl git pkg-config python3 \
        llvm-14 llvm-14-dev clang-14 libclang-14-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

ENV RUSTUP_HOME=/opt/rustup CARGO_HOME=/opt/cargo PATH=/opt/cargo/bin:$PATH
RUN curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --component rustfmt --default-toolchain 1.94.0
ENV LLVM_CONFIG_PATH=/usr/bin/llvm-config-14 LIBCLANG_PATH=/usr/lib/llvm-14/lib
RUN cargo install --locked c2rust --version 0.22.1 && c2rust --version
# Raw C2Rust output uses nightly-only feature gates (e.g. extern_types), so the
# baseline crate is built with this pinned nightly. The libc crate is fetched
# at image build time so baseline builds run offline.
RUN rustup toolchain install nightly-2026-03-01 --profile minimal \
    && cargo new --lib /opt/warm && cd /opt/warm \
    && cargo add libc@0.2 && cargo +nightly-2026-03-01 build \
    && rm -rf /opt/warm

WORKDIR /work
