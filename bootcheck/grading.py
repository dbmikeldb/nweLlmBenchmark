import re

ALLOWED_TOP_LEVEL_LINES = {
    "enable",
    "configure terminal",
    "exit",
    "end",
    "write memory",
    "copy running-config startup-config",
}

SAVE_COMMAND_VARIANTS = {
    "write memory",
    "copy running-config startup-config",
}


def _line_present(response_text: str, target: str) -> bool:
    pattern = rf"^\s*{re.escape(target)}\s*$"
    return bool(re.search(pattern, response_text, re.MULTILINE | re.IGNORECASE))


def _check_isolation(response_text: str, isolation: dict) -> bool:
    expected_interface = isolation.get("interface")
    allowed_prefixes = [p.lower() for p in isolation.get("allowed_top_level_prefixes", [])]

    in_submode = False
    for raw_line in response_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("!"):
            continue

        if line.lower().startswith("interface "):
            if expected_interface is None:
                return False
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

        if line.lower() in ALLOWED_TOP_LEVEL_LINES:
            continue

        if any(line.lower().startswith(prefix) for prefix in allowed_prefixes):
            continue

        return False

    return True


def grade(response_text: str, task: dict) -> dict:
    criteria = task["grading"]["pass_criteria"]

    results = {}

    if "required_lines" in criteria:
        results["required_lines"] = all(
            _line_present(response_text, line) for line in criteria["required_lines"]
        )

    if "required_substrings" in criteria:
        results["required_substrings"] = all(
            substring in response_text for substring in criteria["required_substrings"]
        )

    if "config_saved" in criteria:
        results["config_saved"] = any(
            _line_present(response_text, variant) for variant in SAVE_COMMAND_VARIANTS
        )

    if "isolation" in criteria:
        results["isolation"] = _check_isolation(response_text, criteria["isolation"])

    results["pass"] = all(results.values()) if results else False
    return results
