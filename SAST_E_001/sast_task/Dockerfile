# SAST-E-001 Benchmark Task Container
# Harbor-style terminal branch harness sandbox

FROM python:3.11-slim

LABEL task.id="SAST-E-001"
LABEL task.name="SQL Injection Triage Flask API"
LABEL task.tier="easy"
LABEL task.human_baseline_minutes="10"

# System dependencies
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    jq \
    tree \
    ripgrep \
    && rm -rf /var/lib/apt/lists/*

# Create task directory structure
RUN mkdir -p /task/codebase/app \
             /task/sarif \
             /task/instructions \
             /task/output

# Copy codebase (will be set read-only below)
COPY app/app.py           /task/codebase/app/app.py
COPY app/config.py        /task/codebase/app/config.py
COPY app/requirements.txt /task/codebase/app/requirements.txt

# Copy SARIF output
COPY sarif/sast_e_001.sarif /task/sarif/findings.sarif

# Copy task instruction file (plain text - no special characters)
COPY task.txt /task/instructions/task.txt

# Set read-only permissions on codebase and SARIF
RUN chmod -R 444 /task/codebase \
 && chmod -R 444 /task/sarif \
 && chmod 444 /task/instructions/task.txt \
 && chmod 777 /task/output

# Helper: show task instructions
RUN echo '#!/bin/bash' > /usr/local/bin/show_task \
 && echo 'cat /task/instructions/task.txt' >> /usr/local/bin/show_task \
 && chmod +x /usr/local/bin/show_task

# Helper: pretty-print SARIF findings summary
RUN echo '#!/bin/bash' > /usr/local/bin/show_findings \
 && echo 'echo "=== SARIF FINDINGS SUMMARY ==="' >> /usr/local/bin/show_findings \
 && echo 'cat /task/sarif/findings.sarif | jq -r ".runs[0].results[] | \"Finding \" + (.properties.finding_index | tostring) + \": [\" + (.level | ascii_upcase) + \"] \" + .ruleId + \"\n  File: \" + .locations[0].physicalLocation.artifactLocation.uri + \" line \" + (.locations[0].physicalLocation.region.startLine | tostring) + \"\n  Code: \" + .locations[0].physicalLocation.region.snippet.text + \"\n\""' >> /usr/local/bin/show_findings \
 && echo 'echo "=============================="' >> /usr/local/bin/show_findings \
 && chmod +x /usr/local/bin/show_findings

WORKDIR /task

CMD ["cat", "/task/instructions/task.txt"]
