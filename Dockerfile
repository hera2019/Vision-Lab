# syntax=docker/dockerfile:1
# CPU-only Linux build and runtime for the Vision Lab C++ pipeline.
FROM ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55 AS base

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential cmake ninja-build ca-certificates curl \
      libeigen3-dev \
      libopencv-core-dev libopencv-imgproc-dev libopencv-imgcodecs-dev \
      libopencv-videoio-dev libopencv-video-dev \
    && rm -rf /var/lib/apt/lists/*

# ONNX Runtime prebuilt release, verified by SHA-256.
ARG TARGETARCH
ARG ORT_VERSION=1.30.0
ARG ORT_SHA256_ARM64=e16a27a8ed330bbc698df7330b0cf56e722f354e3bcc92118682c74ef3c3e3da
ARG ORT_SHA256_AMD64=a5ed5a3cac51fbb2e90da632ae43d19212faaa20e76484e62bcb7c23ddb3b3fd
RUN case "${TARGETARCH}" in \
      arm64) ORT_ARCH=aarch64; ORT_SHA256=${ORT_SHA256_ARM64} ;; \
      amd64) ORT_ARCH=x64;     ORT_SHA256=${ORT_SHA256_AMD64} ;; \
      *) echo "unsupported arch: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
    && curl -fsSL -o /tmp/ort.tgz \
      "https://github.com/microsoft/onnxruntime/releases/download/v${ORT_VERSION}/onnxruntime-linux-${ORT_ARCH}-${ORT_VERSION}.tgz" \
    && echo "${ORT_SHA256}  /tmp/ort.tgz" | sha256sum -c - \
    && mkdir -p /opt/onnxruntime \
    && tar -xzf /tmp/ort.tgz -C /opt/onnxruntime --strip-components=1 \
    && rm /tmp/ort.tgz

ENV ONNXRUNTIME_ROOT=/opt/onnxruntime \
    LD_LIBRARY_PATH=/opt/onnxruntime/lib

FROM base AS build
WORKDIR /src
COPY cpp/ cpp/
RUN cmake -S cpp -B build -G Ninja -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build

CMD ["/src/build/env_check"]

# Python tools for ONNX export and evaluation. ByteTrack is mounted at
# /work/external/ByteTrack and put on PYTHONPATH (it is not pip-installed).
FROM ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55 AS pytools
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv ca-certificates build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*
COPY python/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/work/external/ByteTrack \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /work
