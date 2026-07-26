import random
import json


def sample_context(context_blocks_json: str, ratio: float, bias_field: str) -> list[dict]:
    blocks = json.loads(context_blocks_json) if isinstance(context_blocks_json, str) else context_blocks_json
    if not blocks:
        return []
    if ratio >= 1.0:
        sampled = list(blocks)
    else:
        n = max(1, int(len(blocks) * ratio))
        sampled = random.sample(blocks, min(n, len(blocks)))
    result = _apply_bias(sampled, bias_field)
    return result


def _apply_bias(blocks: list[dict], bias_field: str) -> list[dict]:
    if bias_field == "random":
        random.shuffle(blocks)
        return blocks
    if bias_field == "diverse":
        return _maximize_diversity(blocks)
    if bias_field == "all":
        return blocks
    scored = []
    for b in blocks:
        tags = b.get("tags", [])
        content = b.get("content", "").lower()
        register = b.get("register", "").lower()
        score = 0.0
        if bias_field == "success":
            if any(t in ("success", "solution", "verified") for t in tags):
                score += 2.0
            if "implemented" in content or "works" in content:
                score += 1.0
            if register == "fact":
                score += 1.0
        elif bias_field == "failure":
            if any(t in ("failure", "bug", "error", "edge_case") for t in tags):
                score += 2.0
            if "fail" in content or "bug" in content:
                score += 1.0
            if register == "opinion":
                score += 0.5
        elif bias_field == "adversarial":
            if any(t in ("security", "exploit", "vulnerability") for t in tags):
                score += 2.0
            if "attack" in content or "worst" in content:
                score += 1.0
        scored.append((b, score))
    scored.sort(key=lambda x: -x[1])
    return [b for b, _ in scored]


def _maximize_diversity(blocks: list[dict]) -> list[dict]:
    seen_registers = set()
    diverse = []
    remaining = list(blocks)
    random.shuffle(remaining)
    for b in remaining:
        r = b.get("register", "unknown")
        if r not in seen_registers:
            diverse.append(b)
            seen_registers.add(r)
    for b in remaining:
        if b not in diverse:
            diverse.append(b)
    return diverse
