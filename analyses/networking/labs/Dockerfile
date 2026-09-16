# Optional reproducible test environment. The course itself targets a Linux VM.
FROM debian:12-slim
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       bash ca-certificates conntrack curl dnsutils ethtool iperf3 iproute2 \
       iputils-ping iputils-tracepath nftables procps python3 sudo tcpdump traceroute \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /course
COPY . /course/
CMD ["bash"]
