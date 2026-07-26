import json


def build_synthesis_prompt(task: str, responses_json: str) -> str:
    responses = json.loads(responses_json) if isinstance(responses_json, str) else responses_json
    parts = [
        f"Task: {task}",
        "",
        "Below are responses from multiple agents. "
        "Merge the best parts into a single coherent final output.",
        "",
    ]
    for entry in responses:
        parts.append(f"=== {entry.get('role', 'agent').upper()} ===")
        parts.append(entry.get("response", ""))
        parts.append("")
    parts.append(
        "Now produce the FINAL MERGED output. "
        "Resolve any conflicts by majority. "
        "Include the strongest points from each agent. "
        "Output only the final merged response."
    )
    return "\n".join(parts)
