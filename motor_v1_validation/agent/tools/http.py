"""HTTP tool — http_request for API testing."""

import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

REQUEST_TIMEOUT = 30


def tool_http_request(method: str, url: str, headers: dict = None,
                      body: str = "", content_type: str = "application/json") -> str:
    """Make HTTP request via curl. Returns status + body."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    cmd = ['curl', '-s', '--max-time', str(REQUEST_TIMEOUT),
           '-X', method.upper(),
           '-w', '\n---HTTP_STATUS:%{http_code}---',
           url]

    # Add headers
    if headers:
        for k, v in headers.items():
            cmd.extend(['-H', f'{k}: {v}'])

    if content_type and method.upper() in ('POST', 'PUT', 'PATCH'):
        cmd.extend(['-H', f'Content-Type: {content_type}'])

    # Add body
    if body and method.upper() in ('POST', 'PUT', 'PATCH'):
        cmd.extend(['-d', body])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=REQUEST_TIMEOUT + 5)
        if result.returncode != 0:
            return json.dumps({"error": f"curl failed (rc={result.returncode})",
                              "stderr": result.stderr[:500]})

        output = result.stdout
        # Extract HTTP status
        status_code = 0
        if '---HTTP_STATUS:' in output:
            parts = output.rsplit('---HTTP_STATUS:', 1)
            output = parts[0]
            try:
                status_code = int(parts[1].replace('---', '').strip())
            except ValueError:
                pass

        # Try to parse as JSON
        response_body = output.strip()
        try:
            parsed = json.loads(response_body)
            return json.dumps({
                "status": status_code,
                "body": parsed,
                "content_type": "application/json",
            }, indent=2)
        except json.JSONDecodeError:
            return json.dumps({
                "status": status_code,
                "body": response_body[:10000],
                "content_type": "text",
            }, indent=2)

    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Request timed out after {REQUEST_TIMEOUT}s"})
    except Exception as e:
        return json.dumps({"error": f"{type(e).__name__}: {e}"})


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    registry.register("http_request", {
        "name": "http_request",
        "description": "Make HTTP request (GET/POST/PUT/DELETE/PATCH). Returns status + body.",
        "parameters": {"type": "object", "properties": {
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
            "url": {"type": "string", "description": "URL to request"},
            "headers": {"type": "object", "description": "Request headers"},
            "body": {"type": "string", "description": "Request body (for POST/PUT/PATCH)"},
            "content_type": {"type": "string", "description": "Content-Type. Default: application/json"}
        }, "required": ["method", "url"]}
    }, lambda a: tool_http_request(a["method"], a["url"], a.get("headers"),
                                    a.get("body", ""), a.get("content_type", "application/json")),
    category="http")
