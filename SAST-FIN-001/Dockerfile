# SAST-FIN-001 sandbox image.
#
# Layout inside the container:
#   /task/codebase/    Apache Fineract source modules (read-only)
#   /task/sarif/       Semgrep findings SARIF (read-only)
#   /task/instructions task.txt (read-only)
#   /task/output/      writable scratch space (tmpfs at runtime)
#
# IMPORTANT: do not copy oracle/ or harness/ into the image. Those live on the
# host and are only used by the Inspect harness for scoring.

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        coreutils \
        findutils \
        grep \
        less \
        ripgrep \
        sed \
        tree \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /task

# Codebase (subset of Fineract relevant to the 40 findings)
COPY app/ /task/codebase/

# SARIF input
COPY sarif/findings.sarif /task/sarif/findings.sarif

# Agent-visible task instructions
COPY task.txt /task/instructions/task.txt

# Tighten permissions on read-only paths.
RUN chmod -R a-w /task/codebase /task/sarif /task/instructions \
    && mkdir -p /task/output \
    && chmod 0777 /task/output

# Default command keeps the sandbox alive for the harness.
CMD ["sleep", "infinity"]
