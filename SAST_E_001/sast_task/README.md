# SAST-E-001 — Harbor Terminal Branch Harness
## SQL Injection Triage · Easy Tier · ~10 Minute Human Baseline

---

## What This Is

A fully containerised benchmark task that tests whether an LLM can correctly
triage 8 Semgrep SARIF findings in a Python Flask application.

Built on the **Inspect framework** (UK AISI) using a **Harbor style terminal
branch harness** — the agent gets a bash terminal inside a locked Docker
container and can freely explore the codebase before producing structured output.

---

## Directory Structure

```
sast_task/
├── Dockerfile                  # Sandbox container definition
├── run_eval.sh                 # One-command evaluation runner
├── app/
│   ├── app.py                  # Target Flask application (the codebase)
│   └── config.py               # Config with hardcoded secrets (findings 7-8)
├── sarif/
│   └── sast_e_001.sarif        # Pre-generated Semgrep SARIF output
└── harness/
    ├── harness.py              # Inspect task, solver, and scorer
    └── compose.yaml            # Docker sandbox configuration
```

---

## What "Harbor Style Terminal Branch Harness" Means

**Harbor** refers to the containerised sandbox execution pattern used by
Inspect and METR — each evaluation run gets a fresh Docker container
(the Harbor) that is destroyed after the session.

**Terminal** means the agent's primary tool is a bash shell. It can run
any command inside the container — cat, grep, jq, tree, ripgrep.

**Branch** means the agent can explore multiple code paths, run multiple
commands, and investigate multiple files before converging on an answer.
This is opposed to a single-turn solver that gets one prompt and must answer.

The flow looks like this:

```
┌─────────────────────────────────────────────────────────┐
│  Inspect Framework                                       │
│                                                          │
│  ┌──────────┐     ┌──────────┐     ┌──────────────────┐│
│  │  Dataset  │────▶│  Solver  │────▶│  SARIF Scorer    ││
│  │ (1 sample)│     │ (harbor  │     │  F1 + ECE +      ││
│  └──────────┘     │  terminal│     │  Explanation      ││
│                   │  branch) │     └──────────────────┘│
│                   └────┬─────┘                          │
│                        │  bash tool calls               │
│                        ▼                                │
│                ┌───────────────┐                        │
│                │ Docker Sandbox │                       │
│                │               │                        │
│                │ /task/        │                        │
│                │   codebase/   │  ← read-only           │
│                │   sarif/      │  ← read-only           │
│                │   output/     │  ← writable            │
│                │               │                        │
│                │ No internet   │                        │
│                │ No file writes│                        │
│                │ 512MB RAM cap │                        │
│                └───────────────┘                        │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install inspect-ai
# Docker Desktop must be running
```

### 2. Set your API key

```bash
# For Claude
export ANTHROPIC_API_KEY=sk-ant-...

# For GPT-4o
export OPENAI_API_KEY=sk-...

# For Gemini
export GOOGLE_API_KEY=...
```

### 3. Run the evaluation

```bash
chmod +x run_eval.sh

# Run against Claude
./run_eval.sh claude

# Run against GPT-4o
./run_eval.sh gpt

# Run against all models
./run_eval.sh all

# Build the Docker image only (test the container builds)
./run_eval.sh build
```

---

## What the Agent Sees

When the evaluation starts, the agent receives this task prompt:

```
You are a security engineer performing SAST alert triage.

Start by reading the task instructions:
  cat /task/instructions/task.txt

Then explore the codebase and SARIF findings to complete the triage.
Use bash commands freely to read files and understand the code.

When ready, output your classifications for all 8 findings
in the required format, ending with TRIAGE_COMPLETE.
```

The agent then has access to these bash commands inside the container:

```bash
show_task                        # Print task instructions
show_findings                    # Pretty-print all 8 SARIF findings
cat /task/codebase/app/app.py    # Read the Flask application
cat /task/codebase/app/config.py # Read the config file
cat /task/sarif/findings.sarif   # Read raw SARIF JSON
jq '...' /task/sarif/findings.sarif  # Query SARIF with jq
grep -n "query\|execute" /task/codebase/app/app.py
tree /task                       # Show directory structure
```

---

## Ground Truth (Answer Key)

| Finding | Type | CWE | Why |
|---------|------|-----|-----|
| 1 — User.query.filter() | FALSE_POSITIVE | N/A | SQLAlchemy ORM — parameterised automatically |
| 2 — Product.query.filter_by() | FALSE_POSITIVE | N/A | SQLAlchemy ORM — parameterised automatically |
| 3 — Order.query.all() | FALSE_POSITIVE | N/A | ORM call — no injection vector |
| 4 — db.session.query(User) | FALSE_POSITIVE | N/A | SQLAlchemy ORM session — safe |
| 5 — Product.query.get() | FALSE_POSITIVE | N/A | ORM primary key lookup — safe |
| 6 — cursor.execute() + concat | **TRUE_POSITIVE** | CWE-89 | Raw SQL with string concatenation — SQL injection |
| 7 — API_KEY = 'sk-live-...' | **TRUE_POSITIVE** | CWE-798 | Hardcoded live API key in source |
| 8 — DB_PASSWORD = '...' | **TRUE_POSITIVE** | CWE-798 | Hardcoded database password in source |

---

## Scoring

### Pass criteria (both must be met)
- **F1 Score >= 0.75** on the TP/FP classifications
- **Explanation quality >= 75%** (6 of 8 explanations must reference correct code mechanism)

### Metrics produced
- F1 score (primary accuracy metric)
- Precision and recall
- Per-finding accuracy breakdown
- Explanation quality rate
- Tool calls made (agent efficiency signal)
- Overall PASS / FAIL

### Example passing output

A model that correctly classifies all 8 findings:
- F1 = 1.0, Precision = 1.0, Recall = 1.0
- If it calls finding 6 a false positive (misses the SQL injection):
  - Recall drops to 0.5, F1 drops to 0.67 — FAIL

---

## Expected Agent Behaviour (Good Performance)

A well-performing agent will:

1. Read the task instructions and SARIF findings first
2. Identify that findings 1-5 are ORM calls by checking imports
3. Find the `cursor.execute()` call in app.py — real SQL injection
4. Read config.py and find the hardcoded credentials
5. Produce structured output with accurate reasoning per finding
6. Use 5-10 bash tool calls total (efficient exploration)

A poorly-performing agent will:
- Pattern-match on keywords like "query" and flag everything as TP
- Miss the ORM vs raw SQL distinction
- Fail to explain WHY a finding is TP or FP
- Use 0 tool calls (refuses to explore the codebase)

---

## Extending This to Volume

To build 100+ tasks for Phase 1 corpus:

### 1. Source more codebases automatically
```bash
# Clone and scan repos in bulk
for repo in $(cat repo_list.txt); do
    git clone $repo /tmp/repos/$(basename $repo)
    semgrep --config=auto /tmp/repos/$(basename $repo) \
            --sarif \
            --output /corpus/sarif/$(basename $repo).sarif
done
```

### 2. Generate a task for each SARIF file
```python
# Generate Inspect samples from SARIF files
for sarif_file in Path('/corpus/sarif').glob('*.sarif'):
    sample = Sample(
        id=sarif_file.stem,
        input=build_task_prompt(sarif_file),
        target=json.dumps(ground_truth),  # From annotators
    )
```

### 3. Run all tasks in parallel
```bash
inspect eval harness.py@sast_corpus \
    --model anthropic/claude-sonnet-4-6 \
    --sandbox docker \
    --max-tasks 10    # Run 10 containers simultaneously
```

---

## Results Location

Results are saved to `results/` as JSON log files.
View them with:
```bash
./run_eval.sh results      # Show latest results summary
inspect view results/      # Open Inspect's web log viewer
```

---

## Security Notes

The Docker container is hardened for benchmark use:
- **No internet access** (network_mode: none)
- **Read-only filesystem** except /task/output and /tmp
- **No new privileges** (no sudo, no privilege escalation)
- **All capabilities dropped**
- **512MB RAM limit** (prevents runaway cost)
- **Container destroyed after each run** (no state persistence)

This matches the Inspect framework's standard sandbox security profile
and is compatible with METR's HCAST reproducibility requirements.
