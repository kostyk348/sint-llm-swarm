import json
import os
import time

STATS_PATH = os.path.expanduser("~/.config/opencode/swarm/stats.json")


def _load_stats() -> dict:
    if not os.path.exists(STATS_PATH):
        return {"runs": [], "total_runs": 0, "created_at": time.time()}
    try:
        with open(STATS_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"runs": [], "total_runs": 0, "created_at": time.time()}


def _save_stats(stats: dict):
    os.makedirs(os.path.dirname(STATS_PATH), exist_ok=True)
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)


def record_run(task: str, roles: list[str], context_count: int, elapsed: float):
    stats = _load_stats()
    stats.setdefault("runs", [])
    stats["total_runs"] = stats.get("total_runs", 0) + 1
    stats["last_run"] = time.time()
    stats["runs"].append({
        "ts": time.time(),
        "task": task[:100],
        "roles": roles,
        "context_count": context_count,
        "elapsed": round(elapsed, 3),
    })
    if len(stats["runs"]) > 1000:
        stats["runs"] = stats["runs"][-1000:]
    _save_stats(stats)


def get_stats() -> dict:
    stats = _load_stats()
    runs = stats.get("runs", [])
    if not runs:
        return {"total_runs": 0, "avg_elapsed": 0, "avg_roles": 0, "avg_context": 0, "role_freq": {}}
    role_freq = {}
    for r in runs:
        for role in r.get("roles", []):
            role_freq[role] = role_freq.get(role, 0) + 1
    return {
        "total_runs": stats.get("total_runs", 0),
        "avg_elapsed": round(sum(r.get("elapsed", 0) for r in runs) / len(runs), 3),
        "avg_roles": round(sum(len(r.get("roles", [])) for r in runs) / len(runs), 1),
        "avg_context": round(sum(r.get("context_count", 0) for r in runs) / len(runs), 1),
        "role_freq": role_freq,
        "recent_runs": runs[-10:],
    }
