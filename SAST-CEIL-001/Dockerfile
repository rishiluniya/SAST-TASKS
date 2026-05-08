# SAST-CEIL-001 Benchmark Task Container
FROM python:3.11-slim
LABEL task.id="SAST-CEIL-001"
LABEL task.tier="ceiling"
LABEL task.human_baseline_minutes="180"
LABEL task.expected_ai_pass_rate="under_5_percent"
RUN apt-get update && apt-get install -y bash curl jq tree ripgrep && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /task/codebase/app/auth /task/codebase/app/orders /task/codebase/app/payments /task/codebase/app/admin /task/sarif /task/instructions /task/output
COPY app/auth/app.py     /task/codebase/app/auth/app.py
COPY app/orders/app.py   /task/codebase/app/orders/app.py
COPY app/payments/app.py /task/codebase/app/payments/app.py
COPY app/admin/app.py    /task/codebase/app/admin/app.py
COPY sarif/findings.sarif /task/sarif/findings.sarif
COPY task.txt /task/instructions/task.txt
RUN find /task/codebase -type d -exec chmod 555 {} \; && \
    find /task/codebase -type f -exec chmod 444 {} \; && \
    find /task/sarif -type d -exec chmod 555 {} \; && \
    find /task/sarif -type f -exec chmod 444 {} \; && \
    chmod 555 /task/instructions && \
    chmod 444 /task/instructions/task.txt && \
    chmod 777 /task/output
RUN echo '#!/bin/bash' > /usr/local/bin/show_task && echo 'cat /task/instructions/task.txt' >> /usr/local/bin/show_task && chmod +x /usr/local/bin/show_task
RUN echo '#!/bin/bash' > /usr/local/bin/show_findings && echo 'echo "=== FINDINGS (Semgrep + CodeQL, 18 total) ===" && cat /task/sarif/findings.sarif | jq -r ".runs[0].results[] | \"Finding \" + (.properties.finding_index | tostring) + \" [\" + (.properties.tool) + \" \" + (.level | ascii_upcase) + \"]: \" + .ruleId + \"\n  \" + .locations[0].physicalLocation.region.snippet.text + \"\n\""' >> /usr/local/bin/show_findings && echo 'echo "=============================================="' >> /usr/local/bin/show_findings && chmod +x /usr/local/bin/show_findings
WORKDIR /task
CMD ["sleep", "infinity"]