"""sint-llm-swarm — LLM Swarm with SINT-intrinsic roles.

Each role maps to a SINT cognitive layer or inner-loop step.
Agents run in parallel (via task), each with a random context slice.
Results are merged via DSO deterministic merge and validated.

Run: python server.py (stdio)
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from config import NAME, VERSION, ROLES, DEFAULT_CONFIG, CACHE_DIR

mcp = FastMCP(NAME)


# ─── Helpers ─────────────────────────────────────────────────────

def _sample_context(context_blocks: list[dict],
                    ratio: float,
                    bias: str | None = None) -> list[dict]:
    """Sample a random subset of context blocks (bagging).

    If bias is specified, weight sampling toward blocks matching that bias.
    """
    if not context_blocks:
        return []
    k = max(1, int(len(context_blocks) * ratio))

    if bias and bias in ("raw_data", "facts", "errors", "code_tasks"):
        # Simple bias: prefer blocks with matching tags
        biased = [b for b in context_blocks
                  if any(t.lower() == bias for t in b.get("tags", []))]
        if len(biased) >= k:
            return random.sample(biased, k)
        # Fill remaining from unbiased pool
        unbiased = [b for b in context_blocks if b not in biased]
        needed = k - len(biased)
        if unbiased and needed > 0:
            biased.extend(random.sample(unbiased, min(needed, len(unbiased))))
        return biased
    else:
        return random.sample(context_blocks, min(k, len(context_blocks)))


def _build_role_prompt(role: str, task: str, context_slice: list[dict]) -> dict:
    """Build a complete prompt bundle for one agent."""
    role_def = ROLES[role]
    context_text = "\n".join(
        f"[{b.get('register','?')}] {b.get('content','')}"
        for b in context_slice
    )
    return {
        "role": role,
        "role_name": role_def["name"],
        "origin": role_def["origin"],
        "system_prompt": role_def["prompt"],
        "task": task,
        "context": context_text,
        "context_block_count": len(context_slice),
    }


def _merge_results(all_results: list[dict]) -> dict:
    """DSO-inspired deterministic merge of swarm results."""
    merged = {
        "sense_observations": [],
        "register_assignments": [],
        "cognition_inferences": [],
        "metacognition_issues": [],
        "provenance_status": [],
        "temporal_analysis": [],
        "uncertainty_calibration": [],
        "feedback_patterns": [],
    }
    for r in all_results:
        role = r.get("role", "unknown")
        content = r.get("content", "")
        if role == "sense":
            merged["sense_observations"].append(content)
        elif role == "classify":
            merged["register_assignments"].append(content)
        elif role == "cognition":
            merged["cognition_inferences"].append(content)
        elif role == "metacognition":
            merged["metacognition_issues"].append(content)
        elif role == "provenance":
            merged["provenance_status"].append(content)
        elif role == "temporal":
            merged["temporal_analysis"].append(content)
        elif role == "uncertainty":
            merged["uncertainty_calibration"].append(content)
        elif role == "feedback":
            merged["feedback_patterns"].append(content)
    return merged


def _estimate_token_savings(task: str,
                            context_blocks: list[dict],
                            agent_count: int) -> dict:
    """Estimate tokens saved vs monolithic agent."""
    full_context_tokens = len(json.dumps(context_blocks)) // 4
    task_tokens = len(task) // 4
    monolithic = full_context_tokens + task_tokens + 500  # gen overhead

    per_agent = int(full_context_tokens * DEFAULT_CONFIG["context_sample_ratio"])
    swarm_total = (per_agent + task_tokens) * agent_count + 200  # merge overhead

    savings = monolithic - swarm_total
    return {
        "monolithic_estimate": monolithic,
        "swarm_estimate": swarm_total,
        "savings": max(0, savings),
        "savings_pct": round((1 - swarm_total / max(1, monolithic)) * 100, 1),
        "agent_count": agent_count,
        "sample_ratio": DEFAULT_CONFIG["context_sample_ratio"],
    }


# ─── Tools ───────────────────────────────────────────────────────

@mcp.tool()
def llm_swarm_process(task: str,
                      context_blocks_json: str = "[]",
                      enabled_roles: str | None = None,
                      k: int | None = None) -> str:
    """Run full LLM swarm: spawn N SINT-intrinsic agents, each with random context slice.

    Args:
        task: the task or question to process
        context_blocks_json: JSON array of memory blocks [{register, content, tags}]
        enabled_roles: comma-separated role list (default: all 8)
        k: agents per role (default: 1)
    Returns: JSON with all agent prompts + merge + token savings
    """
    try:
        blocks = json.loads(context_blocks_json) if context_blocks_json else []
    except json.JSONDecodeError:
        blocks = []

    roles = (enabled_roles or ",".join(DEFAULT_CONFIG["enabled_roles"])).split(",")
    roles = [r.strip() for r in roles if r.strip() in ROLES]
    if not roles:
        roles = list(ROLES.keys())

    k = k or 1
    ratio = DEFAULT_CONFIG["context_sample_ratio"]

    # Spawn prompts for each agent
    agent_prompts = []
    for role in roles:
        for i in range(k):
            ctx = _sample_context(blocks, ratio, ROLES[role].get("context_bias"))
            prompt = _build_role_prompt(role, task, ctx)
            agent_prompts.append(prompt)

    # Simulate merge (in real use, each prompt becomes a task() call)
    merged = _merge_results([{
        "role": p["role"],
        "content": f"[{p['role_name']}] Task: {p['task']} | Context: {p['context_block_count']} blocks"
    } for p in agent_prompts])

    savings = _estimate_token_savings(task, blocks, len(agent_prompts))

    return json.dumps({
        "swarm": {
            "total_agents": len(agent_prompts),
            "roles_used": roles,
            "total_context_blocks": len(blocks),
            "sample_ratio": ratio,
        },
        "agent_prompts": agent_prompts,
        "merged_results": merged,
        "token_economy": savings,
        "how_to_use": "Pass agent_prompts to task() for parallel execution, then call llm_swarm_debate + llm_swarm_synthesize",
    }, ensure_ascii=False, indent=1)


@mcp.tool()
def llm_swarm_debate(responses_json: str) -> str:
    """Cross-feed all agent responses for one refinement round.

    Each agent sees the other agents' outputs and can revise its own.

    Args:
        responses_json: JSON array of {role, content} from agent outputs
    Returns: JSON with debate prompts (one per agent)
    """
    try:
        responses = json.loads(responses_json) if isinstance(responses_json, str) else responses_json
    except (json.JSONDecodeError, TypeError):
        responses = []

    debate_rounds = []
    for i, r in enumerate(responses):
        others = [resp for j, resp in enumerate(responses) if j != i]
        others_text = "\n\n".join(
            f"=== {o.get('role','?')} ===\n{o.get('content','')}"
            for o in others
        )
        debate_rounds.append({
            "agent": r.get("role", f"agent_{i}"),
            "debate_prompt": f"[DEBATE ROUND]\n\nOther agents said:\n{others_text}\n\nReview their responses. Do you agree? Disagree? Revise your own response based on this input.",
            "original_content": r.get("content", ""),
        })

    return json.dumps({
        "debate_rounds": debate_rounds,
        "total_agents": len(responses),
        "instruction": "Pass each debate_prompt to the corresponding agent via task()",
    }, ensure_ascii=False, indent=1)


@mcp.tool()
def llm_swarm_synthesize(task: str, responses_json: str) -> str:
    """Merge all agent responses into a single coherent output.

    Args:
        task: original task
        responses_json: JSON array of {role, content} from agent outputs
    Returns: JSON with synthesis prompt
    """
    try:
        responses = json.loads(responses_json) if isinstance(responses_json, str) else responses_json
    except (json.JSONDecodeError, TypeError):
        responses = []

    responses_text = "\n\n".join(
        f"--- {r.get('role','?')} ---\n{r.get('content','')}"
        for r in responses
    )

    synthesis_prompt = f"""[SYNTHESIS]
Task: {task}

All agent responses:
{responses_text}

Your job is to merge these into a single coherent output.
- Resolve conflicts by majority or evidence weight
- Preserve uncertainty flags from the UNCERTAINTY layer
- Include provenance status from the PROVENANCE layer
- Flag any METACOGNITION issues that remain unresolved
- Final output must have a clear register assignment"""

    return json.dumps({
        "synthesis_prompt": synthesis_prompt,
        "task": task,
        "source_count": len(responses),
        "instruction": "Pass synthesis_prompt to an LLM for final merge",
    }, ensure_ascii=False, indent=1)


@mcp.tool()
def llm_swarm_roles() -> str:
    """List all SINT-intrinsic roles with descriptions and origins."""
    return json.dumps({
        "total_roles": len(ROLES),
        "roles": {
            name: {
                "name": info["name"],
                "origin": info["origin"],
                "context_bias": info.get("context_bias", "none"),
                "confidence": info["confidence"],
            }
            for name, info in ROLES.items()
        },
        "note": "These roles derive from SINT methodology, not generic agent patterns",
    }, ensure_ascii=False, indent=1)


@mcp.tool()
def llm_swarm_config() -> str:
    """Show current swarm configuration."""
    return json.dumps({
        "server": {"name": NAME, "version": VERSION},
        "config": DEFAULT_CONFIG,
    }, ensure_ascii=False, indent=1)


@mcp.tool()
def llm_swarm_stats() -> str:
    """Swarm execution statistics."""
    stats_file = CACHE_DIR / "swarm_stats.json"
    if stats_file.exists():
        stats = json.loads(stats_file.read_text())
    else:
        stats = {"total_runs": 0, "total_agents_spawned": 0, "roles_frequency": {}}
    return json.dumps(stats, ensure_ascii=False, indent=1)


def _save_stats(run_data: dict):
    """Persist run statistics."""
    stats_file = CACHE_DIR / "swarm_stats.json"
    if stats_file.exists():
        stats = json.loads(stats_file.read_text())
    else:
        stats = {"total_runs": 0, "total_agents_spawned": 0, "roles_frequency": {}}
    stats["total_runs"] += 1
    stats["total_agents_spawned"] += run_data.get("agent_count", 0)
    for role in run_data.get("roles", []):
        stats["roles_frequency"][role] = stats["roles_frequency"].get(role, 0) + 1
    stats["last_run"] = datetime.now(timezone.utc).isoformat()
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    stats_file.write_text(json.dumps(stats, indent=1))


if __name__ == "__main__":
    mcp.run(transport="stdio")
