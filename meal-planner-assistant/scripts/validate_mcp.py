"""
validate_mcp.py — MCP server configuration integrity checks for meal-planner-assistant.

Validates:
  1. Authentication configuration
  2. Authorization configuration
  3. Timeout configuration
  4. Retry configuration
  5. Versioning
  6. Service abstraction
  7. No direct external API usage
  8. Proper tool registration

Exit code 0 = all pass, 1 = failures found.
"""

import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"
TOOLS_DIR = APP_DIR / "tools"
AGENTS_DIR = APP_DIR / "agents"


@dataclass
class Finding:
    field: str
    severity: str
    message: str
    file: str = ""
    line: int = 0


# Known MCP configuration files
MCP_CONFIG_PATHS = [
    PROJECT_ROOT / "opencode.json",
    PROJECT_ROOT / "opencode.jsonc",
    PROJECT_ROOT / "mcp.json",
    PROJECT_ROOT / ".opencode" / "mcp.json",
    PROJECT_ROOT / "agents-cli-manifest.yaml",
]


def _parse_ast(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return None


def _find_mcp_configs() -> list[Path]:
    return [p for p in MCP_CONFIG_PATHS if p.exists()]


def _load_json_config(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


# ---------------------------------------------------------------------------
# 1. Authentication configuration
# ---------------------------------------------------------------------------


def check_authentication() -> list[Finding]:
    findings: list[Finding] = []
    configs = _find_mcp_configs()
    if not configs:
        findings.append(
            Finding(
                field="authentication",
                severity="info",
                message="No MCP configuration files found — if MCP servers are used, ensure auth is configured",
            )
        )
        return findings

    for cfg_path in configs:
        config = _load_json_config(cfg_path)
        if config is None:
            continue

        mcp_servers = config.get("mcp_servers", [])
        if not isinstance(mcp_servers, list):
            mcp_servers = config.get("mcp", {}).get("servers", [])

        for i, server in enumerate(
            mcp_servers if isinstance(mcp_servers, list) else []
        ):
            if not isinstance(server, dict):
                continue
            server_name = server.get("name", f"server_{i}")
            has_auth = (
                "auth" in server
                or "authentication" in server
                or "token" in str(server)
                or "api_key" in str(server).lower()
            )
            if not has_auth:
                findings.append(
                    Finding(
                        field="authentication",
                        severity="warning",
                        message=f"MCP server '{server_name}' has no authentication configured",
                        file=str(cfg_path),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 2. Authorization configuration
# ---------------------------------------------------------------------------


def check_authorization() -> list[Finding]:
    findings: list[Finding] = []
    configs = _find_mcp_configs()
    if not configs:
        return findings

    for cfg_path in configs:
        config = _load_json_config(cfg_path)
        if config is None:
            continue

        mcp_servers = config.get("mcp_servers", [])
        if not isinstance(mcp_servers, list):
            mcp_servers = config.get("mcp", {}).get("servers", [])

        for i, server in enumerate(
            mcp_servers if isinstance(mcp_servers, list) else []
        ):
            if not isinstance(server, dict):
                continue
            server_name = server.get("name", f"server_{i}")
            if not server.get("tools") and not server.get("expose"):
                findings.append(
                    Finding(
                        field="authorization",
                        severity="warning",
                        message=f"MCP server '{server_name}' has no tools/expose list — authorization scope unclear",
                        file=str(cfg_path),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 3. Timeout configuration
# ---------------------------------------------------------------------------


def check_timeout() -> list[Finding]:
    findings: list[Finding] = []
    configs = _find_mcp_configs()
    if not configs:
        return findings

    for cfg_path in configs:
        config = _load_json_config(cfg_path)
        if config is None:
            continue

        mcp_servers = config.get("mcp_servers", [])
        if not isinstance(mcp_servers, list):
            mcp_servers = config.get("mcp", {}).get("servers", [])

        for i, server in enumerate(
            mcp_servers if isinstance(mcp_servers, list) else []
        ):
            if not isinstance(server, dict):
                continue
            server_name = server.get("name", f"server_{i}")
            if "timeout" not in server:
                findings.append(
                    Finding(
                        field="timeout",
                        severity="warning",
                        message=f"MCP server '{server_name}' has no timeout configured — requests may hang indefinitely",
                        file=str(cfg_path),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 4. Retry configuration
# ---------------------------------------------------------------------------


def check_retry() -> list[Finding]:
    findings: list[Finding] = []
    configs = _find_mcp_configs()
    if not configs:
        return findings

    for cfg_path in configs:
        config = _load_json_config(cfg_path)
        if config is None:
            continue

        mcp_servers = config.get("mcp_servers", [])
        if not isinstance(mcp_servers, list):
            mcp_servers = config.get("mcp", {}).get("servers", [])

        for i, server in enumerate(
            mcp_servers if isinstance(mcp_servers, list) else []
        ):
            if not isinstance(server, dict):
                continue
            server_name = server.get("name", f"server_{i}")
            if "retry" not in server:
                findings.append(
                    Finding(
                        field="retry",
                        severity="info",
                        message=f"MCP server '{server_name}' has no retry configured — transient failures may go unhandled",
                        file=str(cfg_path),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 5. Versioning
# ---------------------------------------------------------------------------


def check_versioning() -> list[Finding]:
    findings: list[Finding] = []
    configs = _find_mcp_configs()
    if not configs:
        return findings

    for cfg_path in configs:
        config = _load_json_config(cfg_path)
        if config is None:
            continue

        mcp_servers = config.get("mcp_servers", [])
        if not isinstance(mcp_servers, list):
            mcp_servers = config.get("mcp", {}).get("servers", [])

        for i, server in enumerate(
            mcp_servers if isinstance(mcp_servers, list) else []
        ):
            if not isinstance(server, dict):
                continue
            server_name = server.get("name", f"server_{i}")
            if "version" not in server:
                findings.append(
                    Finding(
                        field="versioning",
                        severity="info",
                        message=f"MCP server '{server_name}' has no version specified — consider adding a version field",
                        file=str(cfg_path),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 6. Service abstraction
# ---------------------------------------------------------------------------


def check_service_abstraction() -> list[Finding]:
    findings: list[Finding] = []
    configs = _find_mcp_configs()
    if not configs:
        return findings

    for cfg_path in configs:
        config = _load_json_config(cfg_path)
        if config is None:
            continue

        mcp_servers = config.get("mcp_servers", [])
        if not isinstance(mcp_servers, list):
            mcp_servers = config.get("mcp", {}).get("servers", [])

        for i, server in enumerate(
            mcp_servers if isinstance(mcp_servers, list) else []
        ):
            if not isinstance(server, dict):
                continue
            server_name = server.get("name", f"server_{i}")
            has_url = bool(server.get("url"))
            has_command = bool(server.get("command"))
            if not has_url and not has_command:
                findings.append(
                    Finding(
                        field="service_abstraction",
                        severity="warning",
                        message=f"MCP server '{server_name}' has no URL or command configured — must specify at least one",
                        file=str(cfg_path),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# 7. No direct external API usage
# ---------------------------------------------------------------------------


def check_no_direct_external_api() -> list[Finding]:
    findings: list[Finding] = []

    for py_file in list(AGENTS_DIR.glob("*.py")) + list(TOOLS_DIR.glob("*.py")):
        tree = _parse_ast(py_file)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ("requests", "httpx", "aiohttp", "urllib"):
                        findings.append(
                            Finding(
                                field="no_direct_external_api",
                                severity="error",
                                message=f"Direct HTTP library '{alias.name}' imported in {py_file.name} — should use MCP or service layer",
                                file=str(py_file),
                                line=node.lineno,
                            )
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module in ("requests", "httpx", "aiohttp"):
                    findings.append(
                        Finding(
                            field="no_direct_external_api",
                            severity="error",
                            message=f"Direct HTTP library '{node.module}' imported in {py_file.name} — should use MCP or service layer",
                            file=str(py_file),
                            line=node.lineno,
                        )
                    )

    return findings


# ---------------------------------------------------------------------------
# 8. Proper tool registration
# ---------------------------------------------------------------------------


def check_tool_registration() -> list[Finding]:
    findings: list[Finding] = []
    configs = _find_mcp_configs()
    if not configs:
        return findings

    tool_functions: set[str] = set()
    if TOOLS_DIR.exists():
        for py_file in TOOLS_DIR.glob("*.py"):
            tree = _parse_ast(py_file)
            if tree is None:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    tool_functions.add(node.name)

    for cfg_path in configs:
        config = _load_json_config(cfg_path)
        if config is None:
            continue

        mcp_servers = config.get("mcp_servers", [])
        if not isinstance(mcp_servers, list):
            mcp_servers = config.get("mcp", {}).get("servers", [])

        for i, server in enumerate(
            mcp_servers if isinstance(mcp_servers, list) else []
        ):
            if not isinstance(server, dict):
                continue
            server_name = server.get("name", f"server_{i}")
            tools = server.get("tools", [])
            if isinstance(tools, list):
                for tool in tools:
                    if isinstance(tool, str) and tool in tool_functions:
                        findings.append(
                            Finding(
                                field="tool_registration",
                                severity="warning",
                                message=f"MCP server '{server_name}' exposes tool '{tool}' that duplicates an in-process tool — prefer one or the other",
                                file=str(cfg_path),
                            )
                        )

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CHECKS: list[tuple[str, str, Any]] = [
    ("Authentication", "warning", check_authentication),
    ("Authorization", "warning", check_authorization),
    ("Timeout", "warning", check_timeout),
    ("Retry", "info", check_retry),
    ("Versioning", "info", check_versioning),
    ("Service abstraction", "warning", check_service_abstraction),
    ("No direct external API", "error", check_no_direct_external_api),
    ("Tool registration", "warning", check_tool_registration),
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
        f"\nMCP validation: {len(errors)} errors, {len(warnings)} warnings, {len(all_findings)} total"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
