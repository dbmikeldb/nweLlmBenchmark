import re

ALLOWED_TOP_LEVEL_LINES = {
    "enable",
    "configure terminal",
    "conf t",
    "exit",
    "end",
    "write memory",
    "wr mem",
    "wr",
    "copy running-config startup-config",
}

SAVE_COMMAND_VARIANTS = {
    "write memory",
    "wr mem",
    "wr",
    "copy running-config startup-config",
}


def _strip_code_fence(response_text: str) -> str:
    match = re.search(r"```[^\n]*\n(.*?)```", response_text, re.DOTALL)
    return match.group(1) if match else response_text


def _line_present(response_text: str, target: str) -> bool:
    pattern = rf"^\s*{re.escape(target)}\s*$"
    return bool(re.search(pattern, response_text, re.MULTILINE | re.IGNORECASE))


def _check_isolation(response_text: str, expected_interface: str) -> bool:
    in_submode = False
    for raw_line in response_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("!"):
            continue

        if line.lower().startswith("interface "):
            submode_interface = line.split(None, 1)[1].strip()
            if submode_interface.lower() != expected_interface.lower():
                return False
            in_submode = True
            continue

        if line.lower() in {"exit", "end"}:
            in_submode = False
            continue

        if in_submode:
            continue

        if line.lower() not in ALLOWED_TOP_LEVEL_LINES:
            return False

    return True


def grade(response_text: str, task: dict) -> dict:
    criteria = task["grading"]["pass_criteria"]
    interface = task["llm_input"]["context"]["interface"]

    results = {
        "interface_admin_up": _line_present(response_text, "no shutdown"),
        "ip_address": criteria["ip_address"].lower() in response_text.lower(),
        "description_exact": criteria["description_exact"] in response_text,
        "hardening_lines": all(
            _line_present(response_text, line) for line in criteria["hardening_lines"]
        ),
        "config_saved": any(
            _line_present(response_text, variant) for variant in SAVE_COMMAND_VARIANTS
        ),
        "isolation": _check_isolation(_strip_code_fence(response_text), interface),
    }

    results["pass"] = all(results.values())
    return results
