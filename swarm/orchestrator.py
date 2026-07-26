import json
import random
import time

from config import DEFAULT_SAMPLE_RATIO, DEFAULT_AGENTS_PER_ROLE
from swarm.roles import get_system_prompt, get_bias_field, is_exclusive_role, list_roles
from swarm.sampler import sample_context
from swarm.debater import build_debate_prompts
from swarm.synthesizer import build_synthesis_prompt
from swarm.stats import record_run


def run_swarm(task: str, context_blocks_json: str, roles: list[str] | None = None, k: int | None = None) -> dict:
    start = time.time()
    if not roles:
        role_defs = list_roles()
        roles = [r["name"] for r in role_defs if not is_exclusive_role(r["name"])]
    if k:
        roles = _expand_to_k(roles, k)
    context_blocks = json.loads(context_blocks_json) if isinstance(context_blocks_json, str) else context_blocks_json
    agent_configs = []

    for role in roles:
        if is_exclusive_role(role):
            continue
        ratio = DEFAULT_SAMPLE_RATIO
        bias = get_bias_field(role)
        sampled = sample_context(context_blocks_json if isinstance(context_blocks_json, str) else json.dumps(context_blocks), ratio, bias)
        system_prompt = get_system_prompt(role)
        agent_prompt = _build_agent_prompt(task, system_prompt, sampled)
        agent_configs.append({
            "role": role,
            "prompt": agent_prompt,
            "system_prompt": system_prompt,
        })

    responses = _spawn_agents(agent_configs)
    debate_prompts = build_debate_prompts(json.dumps(responses))
    refined_responses = _spawn_agents([
        {"role": dp["role"], "prompt": dp["prompt"], "system_prompt": get_system_prompt(dp["role"])}
        for dp in debate_prompts
    ])
    synthesis_prompt = build_synthesis_prompt(task, json.dumps(refined_responses))
    final = _synthesize(synthesis_prompt)
    elapsed = time.time() - start

    record_run(task, roles, len(context_blocks), elapsed)

    return {
        "task": task,
        "roles": roles,
        "agent_responses": responses,
        "debate_responses": refined_responses,
        "final_output": final,
        "elapsed_seconds": elapsed,
    }


def _expand_to_k(roles: list[str], k: int) -> list[str]:
    available = [r for r in roles if not is_exclusive_role(r)]
    if not available:
        return roles
    result = []
    for i in range(k):
        result.append(available[i % len(available)])
    random.shuffle(result)
    return result


def _build_agent_prompt(task: str, system_prompt: str, context_blocks: list[dict]) -> str:
    parts = [system_prompt, "", f"Task: {task}", "", "Relevant context:"]
    for i, block in enumerate(context_blocks):
        parts.append(f"\n[{i}] {json.dumps(block)}")
    parts.append(
        "\n\nProduce your response. Be thorough. "
        "Output only the response content."
    )
    return "\n".join(parts)


def _spawn_agents(configs: list[dict]) -> list[dict]:
    from opencode.context import get_input
    responses = []
    for cfg in configs:
        try:
            result = get_input(cfg["prompt"])
            text = result if isinstance(result, str) else str(result)
        except Exception as e:
            text = f"[ERROR: {e}]"
        responses.append({
            "role": cfg["role"],
            "response": text,
        })
    return responses


def _synthesize(prompt: str) -> str:
    try:
        from opencode.context import get_input
        result = get_input(prompt)
        return result if isinstance(result, str) else str(result)
    except Exception as e:
        return f"[SYNTHESIS ERROR: {e}]"
