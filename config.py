NAME = "sint-llm-swarm-mcp"
VERSION = "0.1.0"

ROLES = {
    "creator": {
        "system_prompt": "You are a CREATOR. Your job is to generate a complete solution. Be thorough and creative. Focus on producing working output.",
        "bias_field": "success",
        "description": "Generates the primary solution — biased toward past successes",
    },
    "critic": {
        "system_prompt": "You are a CRITIC. Your job is to find flaws, edge cases, and improvements. Be constructive but thorough.",
        "bias_field": "failure",
        "description": "Finds flaws and edge cases — biased toward past failures",
    },
    "adversary": {
        "system_prompt": "You are an ADVERSARY. Your job is to break the solution. Find worst-case scenarios, security issues, and failure modes.",
        "bias_field": "adversarial",
        "description": "Stress-tests solutions — biased toward adversarial examples",
    },
    "explorer": {
        "system_prompt": "You are an EXPLORER. Your job is to find ALTERNATIVE approaches. Don't settle for the obvious solution.",
        "bias_field": "diverse",
        "description": "Finds alternative approaches — random diverse context",
    },
    "synthesizer": {
        "system_prompt": "You are a SYNTHESIZER. Your job is to merge the best parts of all responses into a coherent final output.",
        "bias_field": "all",
        "description": "Merges all responses into final output",
        "exclusive": True,
    },
}

DEFAULT_SAMPLE_RATIO = 0.6
DEFAULT_AGENTS_PER_ROLE = 1
DEFAULT_CONTEXT_STRATEGY = "bagging"
