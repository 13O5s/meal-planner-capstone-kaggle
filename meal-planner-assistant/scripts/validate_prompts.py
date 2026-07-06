"""
validate_prompts.py — Prompt integrity checks for meal-planner-assistant.

Validates:
  1. Prompt separation
  2. Prompt injection protections
  3. Secret leakage
  4. Unsupported placeholders
  5. Raw user interpolation
  6. Missing safety instructions

Exit code 0 = all pass, 1 = failures found.
"""

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
AGENTS_DIR = APP_DIR / "agents"
TOOLS_DIR = APP_DIR / "tools"
COORDINATOR_PATH = APP_DIR / "agent.py"


@dataclass
class Finding:
    field: str
    severity: str
    message: str
    file: str = ""
    line: int = 0


HIGH_ENTROPY_THRESHOLD = 0.6

SYS_PROMPT_KEYWORDS = {"system_instruction", "instruction"}
PROMPT_VAR_PATTERN = re.compile(r"\{[A-Za-z_][A-Za-z_0-9]*\}")
DANGEROUS_CHARS = re.compile(r"[<>\{\}]")
PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z_][A-Za-z_0-9]*)\}")

SAFETY_INSTRUCTION_FRAGMENTS = [
    "do not reveal",
    "do not share",
    "confidential",
    "internal use",
    "system prompt",
    "ignore previous",
    "do not output",
    "safety",
    "guideline",
    "boundary",
    "restricted",
    "policy",
]

ENSEMBLE_SAFETY_FRAGMENTS = [
    "do not output",
    "ignore previous",
    "do not follow",
    "you are not",
    "do not execute",
    "do not obey",
]

PROHIBITED_SECRET_PATTERNS = [
    re.compile(r'api_key\s*[:=]\s*["\'](.+?)["\']', re.IGNORECASE),
    re.compile(r'password\s*[:=]\s*["\'](.+?)["\']', re.IGNORECASE),
    re.compile(r'token\s*[:=]\s*["\'](.+?)["\']', re.IGNORECASE),
    re.compile(r'secret\s*[:=]\s*["\'](.+?)["\']', re.IGNORECASE),
    re.compile(r"GOOGLE_API_KEY", re.IGNORECASE),
    re.compile(r"OPENAI_API_KEY", re.IGNORECASE),
    re.compile(r"ANTHROPIC_API_KEY", re.IGNORECASE),
    re.compile(r"AIzaSy[A-Za-z0-9_-]{35}"),
]


def _get_agent_files() -> list[Path]:
    if not AGENTS_DIR.exists():
        return []
    return sorted(AGENTS_DIR.glob("*.py"))


def _parse_ast(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return None


def _extract_all_instructions(file_path: Path) -> list[tuple[str, int]]:
    """Extract all instruction/system_instruction strings from a file."""
    tree = _parse_ast(file_path)
    if tree is None:
        return []

    results: list[tuple[str, int]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords if hasattr(node, "keywords") else []:
                if kw.arg in SYS_PROMPT_KEYWORDS:
                    if isinstance(kw.value, ast.Constant) and isinstance(
                        kw.value.value, str
                    ):
                        results.append((kw.value.value, kw.lineno))
                    elif isinstance(kw.value, ast.JoinedStr):
                        parts: list[str] = []
                        for part in kw.value.values:
                            if isinstance(part, ast.Constant) and isinstance(
                                part.value, str
                            ):
                                parts.append(part.value)
                            elif isinstance(part, ast.FormattedValue):
                                parts.append("{...}")
                        results.append(("".join(parts), kw.lineno))

    return results


# ---------------------------------------------------------------------------
# 1. Prompt separation
# ---------------------------------------------------------------------------


def check_prompt_separation() -> list[Finding]:
    findings: list[Finding] = []

    for agent_file in _get_agent_files():
        text = agent_file.read_text(encoding="utf-8")
        if not text.strip():
            continue

        tree = _parse_ast(agent_file)
        if tree is None:
            continue

        instructions = _extract_all_instructions(agent_file)
        if len(instructions) == 0:
            findings.append(
                Finding(
                    field="prompt_separation",
                    severity="error",
                    message=f"No instruction/system_instruction found in {agent_file.name}",
                    file=str(agent_file),
                )
            )
            continue

        for instr, lineno in instructions:
            if len(instr) < 100:
                findings.append(
                    Finding(
                        field="prompt_separation",
                        severity="warning",
                        message=f"Short instruction ({len(instr)} chars) in {agent_file.name} — may lack sufficient guidance",
                        file=str(agent_file),
                        line=lineno,
                    )
                )

    if COORDINATOR_PATH.exists():
        coord_instructions = _extract_all_instructions(COORDINATOR_PATH)
        if len(coord_instructions) == 0:
            findings.append(
                Finding(
                    field="prompt_separation",
                    severity="warning",
                    message=f"Coordinator at {COORDINATOR_PATH.name} has no instruction — may rely on sub-agent orchestration only",
                    file=str(COORDINATOR_PATH),
                )
            )

    return findings


# ---------------------------------------------------------------------------
# 2. Prompt injection protections
# ---------------------------------------------------------------------------


def _entropy(s: str) -> float:
    if not s:
        return 0.0
    from collections import Counter

    freq = Counter(s)
    import math

    return -sum((count / len(s)) * math.log2(count / len(s)) for count in freq.values())


def check_prompt_injection_protections() -> list[Finding]:
    findings: list[Finding] = []

    for agent_file in _get_agent_files() + (
        [COORDINATOR_PATH] if COORDINATOR_PATH.exists() else []
    ):
        instructions = _extract_all_instructions(agent_file)
        for instr, lineno in instructions:
            instr_lower = instr.lower()

            has_safety = any(
                frag in instr_lower for frag in SAFETY_INSTRUCTION_FRAGMENTS
            )
            has_ensemble = any(
                frag in instr_lower for frag in ENSEMBLE_SAFETY_FRAGMENTS
            )

            if not has_safety:
                findings.append(
                    Finding(
                        field="prompt_injection_protections",
                        severity="warning",
                        message=f"Instruction in {agent_file.name} lacks safety boundary instructions — should include guidelines against prompt injection",
                        file=str(agent_file),
                        line=lineno,
                    )
                )

            high_entropy_segments = [
                line
                for line in instr.split("\n")
                if _entropy(line) > HIGH_ENTROPY_THRESHOLD and len(line) > 20
            ]
            if not has_ensemble and len(high_entropy_segments) > 3:
                findings.append(
                    Finding(
                        field="prompt_injection_protections",
                        severity="warning",
                        message=f"Instruction in {agent_file.name} has {len(high_entropy_segments)} high-entropy segments — consider adding injection guardrails",
                        file=str(agent_file),
                        line=lineno,
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 3. Secret leakage
# ---------------------------------------------------------------------------


def check_secret_leakage() -> list[Finding]:
    findings: list[Finding] = []

    for agent_file in _get_agent_files() + (
        [COORDINATOR_PATH] if COORDINATOR_PATH.exists() else []
    ):
        instructions = _extract_all_instructions(agent_file)
        for instr, lineno in instructions:
            for pattern in PROHIBITED_SECRET_PATTERNS:
                match = pattern.search(instr)
                if match:
                    findings.append(
                        Finding(
                            field="secret_leakage",
                            severity="error",
                            message=f"Potential secret leakage in instruction in {agent_file.name}: matched '{pattern.pattern[:40]}...'",
                            file=str(agent_file),
                            line=lineno,
                        )
                    )
                    break

    return findings


# ---------------------------------------------------------------------------
# 4. Unsupported placeholders
# ---------------------------------------------------------------------------


def check_unsupported_placeholders() -> list[Finding]:
    findings: list[Finding] = []

    for agent_file in _get_agent_files() + (
        [COORDINATOR_PATH] if COORDINATOR_PATH.exists() else []
    ):
        instructions = _extract_all_instructions(agent_file)
        for instr, lineno in instructions:
            placeholders = PLACEHOLDER_PATTERN.findall(instr)
            if placeholders:
                findings.append(
                    Finding(
                        field="unsupported_placeholders",
                        severity="warning",
                        message=f"Instruction in {agent_file.name} uses placeholder variables {placeholders} — ensure they are safe and documented",
                        file=str(agent_file),
                        line=lineno,
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 5. Raw user interpolation
# ---------------------------------------------------------------------------


def check_raw_user_interpolation() -> list[Finding]:
    findings: list[Finding] = []

    for agent_file in _get_agent_files() + (
        [COORDINATOR_PATH] if COORDINATOR_PATH.exists() else []
    ):
        tree = _parse_ast(agent_file)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                has_user_var = False
                for part in node.values:
                    if isinstance(part, ast.FormattedValue):
                        if isinstance(part.value, ast.Name) and (
                            "user" in part.value.id.lower()
                            or "input" in part.value.id.lower()
                        ):
                            has_user_var = True
                        elif isinstance(part.value, ast.Attribute) and (
                            "user" in part.value.attr.lower()
                            or "input" in part.value.attr.lower()
                        ):
                            has_user_var = True
                if has_user_var:
                    findings.append(
                        Finding(
                            field="raw_user_interpolation",
                            severity="error",
                            message=f"Raw user input interpolated into f-string in {agent_file.name} — potential prompt injection vector",
                            file=str(agent_file),
                            line=node.lineno,
                        )
                    )

    return findings


# ---------------------------------------------------------------------------
# 6. Missing safety instructions
# ---------------------------------------------------------------------------


def check_missing_safety_instructions() -> list[Finding]:
    findings: list[Finding] = []

    for agent_file in _get_agent_files() + (
        [COORDINATOR_PATH] if COORDINATOR_PATH.exists() else []
    ):
        instructions = _extract_all_instructions(agent_file)
        for instr, lineno in instructions:
            instr_lower = instr.lower()

            has_output_guard = (
                "do not output" in instr_lower
                or "do not reveal" in instr_lower
                or "do not share" in instr_lower
            )
            has_role_guard = "you are a" in instr_lower or "you are an" in instr_lower

            if not has_role_guard:
                findings.append(
                    Finding(
                        field="missing_safety_instructions",
                        severity="info",
                        message=f"Instruction in {agent_file.name} does not establish agent role — consider adding 'You are a...' system prompt",
                        file=str(agent_file),
                        line=lineno,
                    )
                )

            if not has_output_guard:
                findings.append(
                    Finding(
                        field="missing_safety_instructions",
                        severity="warning",
                        message=f"Instruction in {agent_file.name} lacks output boundary guard ('do not output/reveal')",
                        file=str(agent_file),
                        line=lineno,
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CHECKS: list[tuple[str, str, Any]] = [
    ("Prompt separation", "error", check_prompt_separation),
    ("Prompt injection protections", "warning", check_prompt_injection_protections),
    ("Secret leakage", "error", check_secret_leakage),
    ("Unsupported placeholders", "warning", check_unsupported_placeholders),
    ("Raw user interpolation", "error", check_raw_user_interpolation),
    ("Missing safety instructions", "warning", check_missing_safety_instructions),
]


def main() -> int:
    all_findings: list[Finding] = []
    for check_name, _severity, check_func in CHECKS:
        try:
            findings = check_func()
            if findings:
                for f in findings:
                    tag = (
                        "FAIL"
                        if f.severity == "error"
                        else "WARN"
                        if f.severity == "warning"
                        else "INFO"
                    )
                    loc = f" [{f.file}" + (f":{f.line}" if f.line else "") + "]"
                    print(f"  [{tag}] {f.field}: {f.message}{loc}")
                all_findings.extend(findings)
        except Exception as e:
            print(f"  [ERROR] {check_name} crashed: {e}", file=sys.stderr)
            all_findings.append(
                Finding(
                    field=check_name, severity="error", message=f"Checker crashed: {e}"
                )
            )

    errors = [f for f in all_findings if f.severity == "error"]
    warnings = [f for f in all_findings if f.severity == "warning"]

    print(
        f"\nPrompt validation: {len(errors)} errors, {len(warnings)} warnings, {len(all_findings)} total"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
