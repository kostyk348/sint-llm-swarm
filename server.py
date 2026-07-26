from fastmcp import FastMCP

from config import NAME, VERSION
from swarm.orchestrator import run_swarm
from swarm.debater import build_debate_prompts
from swarm.synthesizer import build_synthesis_prompt
from swarm.roles import list_roles
from swarm.stats import get_stats
from config import DEFAULT_SAMPLE_RATIO, DEFAULT_AGENTS_PER_ROLE, DEFAULT_CONTEXT_STRATEGY

mcp = FastMCP(NAME, version=VERSION)


@mcp.tool()
def llm_swarm_process(task: str, context_blocks_json: str, roles: str | None = None, k: int | None = None) -> dict:
    """Run full LLM swarm: spawn agents with different roles and random context slices -> debate -> synthesize -> output.

    Args:
        task: The task description.
        context_blocks_json: JSON string of context blocks (list of dicts with content, tags, register).
        roles: Optional JSON list of role names, e.g. '["creator","critic"]'. Default: all non-exclusive roles.
        k: Optional total number of agents to spawn (roles are cycled). Default: one per selected role.
    """
    import json
    parsed_roles = None
    if roles:
        parsed_roles = json.loads(roles) if isinstance(roles, str) else roles
    return run_swarm(task, context_blocks_json, roles=parsed_roles, k=k)


@mcp.tool()
def llm_swarm_debate(responses_json: str) -> list[dict]:
    """Build debate prompts: each agent reviews others' responses. Returns refined prompts.

    Args:
        responses_json: JSON string of agent responses, e.g. [{"role":"creator","response":"..."}].
    """
    return build_debate_prompts(responses_json)


@mcp.tool()
def llm_swarm_synthesize(task: str, responses_json: str) -> str:
    """Build a synthesis prompt that merges all agent responses into a single final output.

    Args:
        task: The original task.
        responses_json: JSON string of agent responses.
    """
    return build_synthesis_prompt(task, responses_json)


@mcp.tool()
def llm_swarm_roles() -> list[dict]:
    """List all available swarm roles with descriptions."""
    return list_roles()


@mcp.tool()
def llm_swarm_config() -> dict:
    """Show current swarm configuration: sample ratio, agents per role, context strategy."""
    return {
        "sample_ratio": DEFAULT_SAMPLE_RATIO,
        "agents_per_role": DEFAULT_AGENTS_PER_ROLE,
        "context_strategy": DEFAULT_CONTEXT_STRATEGY,
        "version": VERSION,
    }


@mcp.tool()
def llm_swarm_stats() -> dict:
    """Return swarm statistics: total runs, avg latency, role frequency, recent runs."""
    return get_stats()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
