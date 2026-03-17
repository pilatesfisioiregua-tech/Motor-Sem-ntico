"""Docker tools — docker_build, docker_run, docker_inspect."""

import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

DOCKER_TIMEOUT = 120


def _has_docker() -> bool:
    try:
        subprocess.run(["docker", "info"], capture_output=True, timeout=5)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_docker(args: list, timeout: int = None) -> str:
    try:
        result = subprocess.run(
            ["docker"] + args,
            capture_output=True, text=True,
            timeout=timeout or DOCKER_TIMEOUT
        )
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        if result.returncode != 0:
            return f"ERROR: docker {' '.join(args)} failed (rc={result.returncode})\n{output[:5000]}"
        return output.strip()[:10000]
    except subprocess.TimeoutExpired:
        return f"ERROR: docker {' '.join(args)} timed out"
    except FileNotFoundError:
        return "ERROR: Docker not found. Install Docker first."


def tool_docker_build(path: str = ".", tag: str = "", dockerfile: str = "") -> str:
    """Build a Docker image."""
    if not _has_docker():
        return "ERROR: Docker not available."
    args = ["build"]
    if tag:
        args.extend(["-t", tag])
    if dockerfile:
        args.extend(["-f", dockerfile])
    args.append(path)
    return _run_docker(args, timeout=300)


def tool_docker_run(image: str, cmd: str = "", ports: str = "",
                    detach: bool = False, rm: bool = True) -> str:
    """Run a Docker container."""
    if not _has_docker():
        return "ERROR: Docker not available."
    args = ["run"]
    if rm:
        args.append("--rm")
    if detach:
        args.append("-d")
    if ports:
        for port_map in ports.split(","):
            args.extend(["-p", port_map.strip()])
    args.append(image)
    if cmd:
        args.extend(cmd.split())
    return _run_docker(args)


def tool_docker_inspect(container: str = "", image: str = "") -> str:
    """Inspect a container or image. Returns JSON details."""
    if not _has_docker():
        return "ERROR: Docker not available."
    if container:
        # Get container logs + status
        logs = _run_docker(["logs", "--tail", "50", container], timeout=10)
        status = _run_docker(["inspect", "--format",
                              "{{.State.Status}} {{.State.StartedAt}}", container], timeout=10)
        ports = _run_docker(["port", container], timeout=10)
        return json.dumps({
            "container": container,
            "status": status,
            "ports": ports,
            "logs": logs[:5000],
        }, indent=2)
    elif image:
        inspect = _run_docker(["image", "inspect", image], timeout=10)
        return inspect[:10000]
    # List running containers
    return _run_docker(["ps", "--format", "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"])


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    registry.register("docker_build", {
        "name": "docker_build",
        "description": "Build a Docker image from Dockerfile.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Build context path. Default: '.'"},
            "tag": {"type": "string", "description": "Image tag (e.g. myapp:latest)"},
            "dockerfile": {"type": "string", "description": "Path to Dockerfile"}
        }, "required": []}
    }, lambda a: tool_docker_build(a.get("path", "."), a.get("tag", ""), a.get("dockerfile", "")),
    category="docker")

    registry.register("docker_run", {
        "name": "docker_run",
        "description": "Run a Docker container.",
        "parameters": {"type": "object", "properties": {
            "image": {"type": "string", "description": "Image to run"},
            "cmd": {"type": "string", "description": "Command to run in container"},
            "ports": {"type": "string", "description": "Port mappings (e.g. '8080:80,5432:5432')"},
            "detach": {"type": "boolean", "description": "Run in background"}
        }, "required": ["image"]}
    }, lambda a: tool_docker_run(a["image"], a.get("cmd", ""), a.get("ports", ""),
                                  a.get("detach", False)), category="docker")

    registry.register("docker_inspect", {
        "name": "docker_inspect",
        "description": "Inspect a container (logs, status, ports) or list running containers.",
        "parameters": {"type": "object", "properties": {
            "container": {"type": "string", "description": "Container ID or name"},
            "image": {"type": "string", "description": "Image to inspect"}
        }, "required": []}
    }, lambda a: tool_docker_inspect(a.get("container", ""), a.get("image", "")),
    category="docker")
