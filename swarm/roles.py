from config import ROLES


def list_roles():
    return [
        {"name": name, "description": info["description"]}
        for name, info in ROLES.items()
    ]


def get_role(name: str) -> dict | None:
    return ROLES.get(name)


def get_system_prompt(name: str) -> str:
    role = ROLES.get(name)
    if not role:
        raise ValueError(f"Unknown role: {name}")
    return role["system_prompt"]


def get_bias_field(name: str) -> str:
    role = ROLES.get(name)
    if not role:
        raise ValueError(f"Unknown role: {name}")
    return role.get("bias_field", "random")


def is_exclusive_role(name: str) -> bool:
    role = ROLES.get(name)
    return role.get("exclusive", False) if role else False
