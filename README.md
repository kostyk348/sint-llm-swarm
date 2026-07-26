# sint-llm-swarm-mcp

**LLM Swarm** — spawns multiple LLM agents in parallel, each with a different role and a random slice of context (bagging). Collects results, runs a debate round, and synthesizes a final output.

Token-efficient because each agent sees **less context** than one monolithic agent would.

## Architecture

```
Input (task + context blocks)
        │
        ▼
  ┌─────────────────────────┐
  │  Sampler (bagging 60%)  │
  │  per-role bias applied   │
  └────────┬────────────────┘
           │
    ┌──────┴──────┐
    ▼  ▼  ▼  ▼  ▼  ▼
  Creator Critic Adv Explorer ...
    │    │    │    │    │
    └────┴────┴────┴────┘
           │ debate round
           ▼
    ┌──────────────┐
    │  Synthesizer  │
    └──────┬───────┘
           ▼
       Final output
           │
           ▼
    DSO Validator (external)
```

## Roles

| Role | Bias | Goal |
|------|------|------|
| Creator | Success | Generate the best first-attempt solution |
| Critic | Failure | Find flaws, edge cases, improvements |
| Adversary | Adversarial | Break the solution, stress-test |
| Explorer | Diverse | Find alternative approaches |
| Synthesizer | All (exclusive) | Merge responses into final output |

## Tools

| Tool | Description |
|------|-------------|
| `llm_swarm_process` | Full swarm pipeline: spawn → debate → synthesize |
| `llm_swarm_debate` | Build cross-review debate prompts |
| `llm_swarm_synthesize` | Build merge prompt |
| `llm_swarm_roles` | List available roles |
| `llm_swarm_config` | Show current configuration |
| `llm_swarm_stats` | Swarm statistics |

## Usage

```python
from swarm.orchestrator import run_swarm

result = run_swarm(
    task="Implement a binary search tree in C",
    context_blocks_json='[{"content":"...", "tags":["success"]}]',
    roles=["creator", "critic", "adversary", "explorer"],
    k=4,
)
print(result["final_output"])
```
