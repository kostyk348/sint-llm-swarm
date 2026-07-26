import json


def build_debate_prompts(responses_json: str) -> list[dict]:
    responses = json.loads(responses_json) if isinstance(responses_json, str) else responses_json
    review_prompts = []
    for i, entry in enumerate(responses):
        role = entry.get("role", "agent")
        response_text = entry.get("response", "")
        other_responses = [
                {"role": r["role"], "response": r["response"]}
                for j, r in enumerate(responses)
                if j != i
        ]
        prompt_parts = [
            f"You are a {role.upper()}. Here is your original response:",
            response_text,
            "",
            "Review the following responses from other agents and refine your own:",
        ]
        for o in other_responses:
            prompt_parts.append(f"\n--- {o['role'].upper()} ---\n{o['response']}")
        prompt_parts.append(
            "\n\nNow produce your REFINED response. "
            "Incorporate valid points from others. "
            "Defend your position where you disagree. "
            "Output only the refined response."
        )
        review_prompts.append({
            "role": role,
            "prompt": "\n".join(prompt_parts),
        })
    return review_prompts
