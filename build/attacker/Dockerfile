FROM registry.access.redhat.com/ubi9/ubi-minimal:latest

USER 0

RUN microdnf install -y bash nmap-ncat jq tar gzip && microdnf clean all

# ttyd for web terminal — pinned to 1.7.7 with SHA256 verification
ARG TTYD_VERSION=1.7.7
ARG TTYD_SHA256=8a217c968aba172e0dbf3f34447218dc015bc4d5e59bf51db2f2cd12b7be4f55
RUN curl -fsSL -o /usr/local/bin/ttyd \
    "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/ttyd.x86_64" && \
    echo "${TTYD_SHA256}  /usr/local/bin/ttyd" | sha256sum -c - && \
    chmod +x /usr/local/bin/ttyd

RUN mkdir -p /usr/local/lib/attacker /data/payloads

COPY scripts/ /usr/local/lib/attacker/
COPY motd.sh /etc/profile.d/motd.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY payloads/ /data/payloads/
COPY prompts.json /data/prompts.json

RUN chmod +x /usr/local/bin/entrypoint.sh \
    /usr/local/lib/attacker/*.sh \
    /etc/profile.d/motd.sh

ENV PATH="/usr/local/lib/attacker:$PATH"

USER 1001

EXPOSE 7681

CMD ["/usr/local/bin/entrypoint.sh"]
