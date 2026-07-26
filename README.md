# sint-llm-swarm

**LLM Swarm with SINT-Intrinsic Roles**

Not generic creator/critic/adversary. Every role derives from SINT methodology:

| Role | SINT Origin | Function |
|------|-------------|----------|
| **SENSE** | Inner Loop Step 1 | Pure observation, no interpretation |
| **CLASSIFY** | Inner Loop Step 2 | Register assignment (SENSE/FACT/LOGIC/OPINION/CAUSALITY) |
| **COGNITION** | Cognitive Layer 2 | Logical deduction from explicit premises |
| **METACOGNITION** | Cognitive Layer 5 | Detect drift, overconfidence, circular reasoning |
| **PROVENANCE** | Invariant 1.5 | Trace every claim to source |
| **TEMPORAL** | DSO + Manifesto | Causality, ordering, tick boundaries |
| **UNCERTAINTY** | Invariant 1.4 | Calibrate confidence per claim |
| **FEEDBACK** | Cognitive Layer 7 | Check against past patterns and errors |

## How it works

1. `llm_swarm_process` — spawns prompts for all roles, each with a *different random 60% slice* of context (bagging)
2. Each prompt → `task()` call for parallel LLM execution
3. `llm_swarm_debate` — cross-feed responses for refinement
4. `llm_swarm_synthesize` — merge into final output
5. Token savings: each agent sees 60% of context → ~40% fewer tokens than monolithic agent

## Tools

| Tool | Description |
|------|-------------|
| `llm_swarm_process` | Full swarm: prompts for all roles with random context slices |
| `llm_swarm_debate` | Cross-feed responses for one refinement round |
| `llm_swarm_synthesize` | Merge all responses into single output |
| `llm_swarm_roles` | List all SINT-intrinsic roles |
| `llm_swarm_config` | Show configuration |
| `llm_swarm_stats` | Execution statistics |
