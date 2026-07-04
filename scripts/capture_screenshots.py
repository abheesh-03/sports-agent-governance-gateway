"""Capture real README screenshots from the running FastAPI app.

This is a development-only helper (see requirements-dev.txt). It is NOT part of
the production runtime. It:

  1. Starts the FastAPI app with Uvicorn on 127.0.0.1:8000 (isolated temp DB).
  2. Waits until /health responds.
  3. Captures the Swagger UI at /docs.
  4. Calls the real API endpoints (blocked request, pending approval, etc.).
  5. Renders each JSON response into a clean HTML page under
     docs/screenshots/_pages/.
  6. Screenshots those pages into docs/screenshots/*.png.
  7. Stops the server cleanly.

Run with:

    python scripts/capture_screenshots.py

Requires the browser binary once:

    pip install -r requirements-dev.txt
    playwright install chromium
"""
import glob
import html
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
SHOTS_DIR = ROOT / "docs" / "screenshots"
PAGES_DIR = SHOTS_DIR / "_pages"
BASE_URL = "http://127.0.0.1:8000"

# Isolated database so the audit log only reflects this run's requests.
TEMP_DB = ROOT / ".screenshots_tmp.db"


def render_page_html(
    title: str,
    method: str,
    endpoint: str,
    request_body,
    status_code: int,
    response_body,
) -> str:
    """Render a clean, white, monospace page for one API interaction."""
    method_color = {"GET": "#1a7f37", "POST": "#0969da"}.get(method, "#57606a")

    request_section = ""
    if request_body is not None:
        req_json = html.escape(json.dumps(request_body, indent=2))
        request_section = f"""
        <div class="label">Request payload</div>
        <pre class="code">{req_json}</pre>
        """

    resp_json = html.escape(json.dumps(response_body, indent=2))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{html.escape(title)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #eef1f5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #1f2328;
    padding: 32px;
  }}
  .card {{
    max-width: 820px;
    margin: 0 auto;
    background: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(27, 31, 36, 0.08);
    padding: 28px 32px 32px;
  }}
  h1 {{
    font-size: 22px;
    margin: 0 0 4px;
  }}
  .subtitle {{
    color: #57606a;
    font-size: 14px;
    margin: 0 0 20px;
  }}
  .endpoint {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
    font-size: 14px;
  }}
  .method {{
    color: #ffffff;
    background: {method_color};
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0.4px;
  }}
  .path {{ color: #1f2328; }}
  .status {{
    margin-left: auto;
    color: #1a7f37;
    font-weight: 600;
  }}
  .label {{
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-size: 11px;
    font-weight: 700;
    color: #57606a;
    margin: 18px 0 8px;
  }}
  .code {{
    background: #f6f8fa;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 16px;
    margin: 0;
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;
    font-size: 13px;
    line-height: 1.55;
    color: #1f2328;
    white-space: pre-wrap;
    word-break: break-word;
  }}
</style>
</head>
<body>
  <div class="card">
    <h1>{html.escape(title)}</h1>
    <p class="subtitle">Sports Agent Governance Gateway &mdash; Northstar Athletics (fictional)</p>
    <div class="endpoint">
      <span class="method">{html.escape(method)}</span>
      <span class="path">{html.escape(endpoint)}</span>
      <span class="status">HTTP {status_code}</span>
    </div>
    {request_section}
    <div class="label">Response</div>
    <pre class="code">{resp_json}</pre>
  </div>
</body>
</html>
"""


def _swagger_asset_dir():
    """Return the local swagger-ui asset directory, or None if unavailable."""
    try:
        import swagger_ui_bundle  # noqa
    except ImportError:
        return None
    base = Path(swagger_ui_bundle.__file__).resolve().parent
    matches = sorted(base.glob("vendor/swagger-ui-*/swagger-ui.css"))
    return matches[-1].parent if matches else None


def build_offline_swagger_html() -> str:
    """Build a self-contained Swagger UI page from the app's real OpenAPI spec.

    Used when the live /docs page cannot load its CDN assets (e.g. restricted
    network). It renders the exact OpenAPI spec served by the running app using
    a locally bundled swagger-ui, so the screenshot is still real — just offline.

    Assets are copied next to the page and referenced by relative URL (the
    canonical swagger-ui-dist setup) rather than inlined, so a literal
    "</script>" inside the minified bundle can't break the page.
    """
    asset_dir = _swagger_asset_dir()
    if asset_dir is None:
        raise RuntimeError(
            "swagger-ui assets not found. Install with: pip install swagger-ui-bundle"
        )
    spec = requests.get(f"{BASE_URL}/openapi.json", timeout=5).json()

    # The vendored swagger-ui (4.x) renders OpenAPI 3.0.x. FastAPI emits 3.1.0,
    # which it rejects ("does not specify a valid version field"). Coerce the
    # version label for rendering only; the app's real spec is unchanged.
    if str(spec.get("openapi", "")).startswith("3.1"):
        spec["openapi"] = "3.0.3"

    # Copy the vendored assets alongside the generated page.
    for asset in ("swagger-ui.css", "swagger-ui-bundle.js",
                  "swagger-ui-standalone-preset.js"):
        shutil.copyfile(asset_dir / asset, PAGES_DIR / asset)

    # Embed the spec directly; escape "<" so the JSON can't close the script tag.
    spec_json = json.dumps(spec).replace("<", "\\u003c")
    title = html.escape(spec.get("info", {}).get("title", "API"))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{title} - Swagger UI</title>
<link rel="stylesheet" href="swagger-ui.css" />
</head>
<body>
<div id="swagger-ui"></div>
<script src="swagger-ui-bundle.js"></script>
<script src="swagger-ui-standalone-preset.js"></script>
<script>
window.ui = SwaggerUIBundle({{
  spec: {spec_json},
  dom_id: '#swagger-ui',
  deepLinking: true,
  validatorUrl: null,
  presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
  layout: 'StandaloneLayout'
}});
</script>
</body>
</html>
"""


def wait_for_health(timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=2)
            if resp.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise RuntimeError("FastAPI app did not become healthy in time.")


def collect_interactions():
    """Call the real API and return the list of pages to screenshot.

    Order matters: the blocked request and the ticket-hold request must run
    before the audit-log and pending-approvals captures.
    """
    interactions = []

    # 1. GET /tools
    r = requests.get(f"{BASE_URL}/tools", timeout=5)
    interactions.append(
        dict(
            filename="tools-endpoint.png",
            title="Registered Tools",
            method="GET",
            endpoint="/tools",
            request_body=None,
            status_code=r.status_code,
            response_body=r.json(),
        )
    )

    # 2. Blocked request: guest tries a protected fan-profile lookup.
    blocked_payload = {
        "user_id": "guest_001",
        "user_role": "guest",
        "tool_name": "lookup_fan_profile",
        "input_payload": {"fan_id": "fan_001"},
    }
    r = requests.post(f"{BASE_URL}/tools/call", json=blocked_payload, timeout=5)
    interactions.append(
        dict(
            filename="blocked-request.png",
            title="Blocked Request Example",
            method="POST",
            endpoint="/tools/call",
            request_body=blocked_payload,
            status_code=r.status_code,
            response_body=r.json(),
        )
    )

    # 3. Pending approval: ticketing manager requests a high-risk ticket hold.
    hold_payload = {
        "user_id": "manager_001",
        "user_role": "ticketing_manager",
        "tool_name": "request_ticket_hold",
        "input_payload": {"ticket_id": "tix_5001", "seat_count": 2},
    }
    r = requests.post(f"{BASE_URL}/tools/call", json=hold_payload, timeout=5)
    interactions.append(
        dict(
            filename="pending-approval.png",
            title="High-Risk Action Routed for Approval",
            method="POST",
            endpoint="/tools/call",
            request_body=hold_payload,
            status_code=r.status_code,
            response_body=r.json(),
        )
    )

    # 4. GET /audit-logs (now reflects the two requests above).
    r = requests.get(f"{BASE_URL}/audit-logs", timeout=5)
    interactions.append(
        dict(
            filename="audit-logs.png",
            title="Audit Logs",
            method="GET",
            endpoint="/audit-logs",
            request_body=None,
            status_code=r.status_code,
            response_body=r.json(),
        )
    )

    # 5. GET /approvals/pending (the ticket hold is waiting for review).
    r = requests.get(f"{BASE_URL}/approvals/pending", timeout=5)
    interactions.append(
        dict(
            filename="pending-approvals.png",
            title="Pending Approvals",
            method="GET",
            endpoint="/approvals/pending",
            request_body=None,
            status_code=r.status_code,
            response_body=r.json(),
        )
    )

    # 6. Successful agent request: a natural-language message is routed through
    #    the governed tools. Captured last so its tool calls do not appear in the
    #    audit-logs screenshot above.
    agent_payload = {
        "user_id": "user_123",
        "user_role": "fan_support_agent",
        "message": "Find two tickets for the next game and tell me the bag policy.",
    }
    r = requests.post(f"{BASE_URL}/agent/request", json=agent_payload, timeout=5)
    interactions.append(
        dict(
            filename="successful-agent-request.png",
            title="Successful Agent Request",
            method="POST",
            endpoint="/agent/request",
            request_body=agent_payload,
            status_code=r.status_code,
            response_body=r.json(),
        )
    )

    return interactions


def _find_chromium_executable():
    """Return a pre-installed chromium path if the default is unavailable.

    Some environments ship a browser build that differs from the pip package's
    expected revision. In that case we point Playwright at the existing binary
    instead of downloading a new one. Locally (after ``playwright install``)
    this returns None so Playwright uses its own managed browser.
    """
    browsers_dir = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    matches = sorted(
        glob.glob(os.path.join(browsers_dir, "chromium-*", "chrome-linux", "chrome"))
    )
    return matches[-1] if matches else None


def capture(interactions) -> None:
    from playwright.sync_api import sync_playwright

    # No browser proxy: the only external assets are the live /docs CDN files,
    # and when those are unreachable we fall back to a fully local, self-contained
    # Swagger page. Routing the browser through a proxy would otherwise interfere
    # with loading those local file:// assets.
    launch_kwargs = {}

    executable = _find_chromium_executable()
    if executable:
        launch_kwargs["executable_path"] = executable

    # Container-safe flags. "--js-flags=--jitless" is important in hardened
    # sandboxes: V8's JIT allocates executable memory (PROT_EXEC mmap), which a
    # seccomp policy may block by killing the process. Heavy JS pages like the
    # Swagger UI trigger this; running JIT-less renders them interpreted instead.
    launch_kwargs["args"] = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--js-flags=--jitless",
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        context = browser.new_context(
            viewport={"width": 1000, "height": 900},
            device_scale_factor=2,
            ignore_https_errors=True,
        )
        page = context.new_page()

        # Rendered JSON interaction pages (lightweight, always reliable).
        for item in interactions:
            html_str = render_page_html(
                title=item["title"],
                method=item["method"],
                endpoint=item["endpoint"],
                request_body=item["request_body"],
                status_code=item["status_code"],
                response_body=item["response_body"],
            )
            page_path = PAGES_DIR / (item["filename"].replace(".png", ".html"))
            page_path.write_text(html_str, encoding="utf-8")
            page.goto(page_path.as_uri(), wait_until="load")
            page.wait_for_timeout(300)
            page.screenshot(path=str(SHOTS_DIR / item["filename"]), full_page=True)
            print(f"  captured {item['filename']}")

        # Swagger UI last. Try the live /docs first (works when the CDN is
        # reachable); if its assets do not render, fall back to a self-contained
        # page built from the app's real OpenAPI spec + local swagger-ui assets.
        # Each attempt uses a fresh page so a failed attempt cannot leave state
        # that breaks the next one.
        captured = False
        live_page = context.new_page()
        try:
            live_page.goto(f"{BASE_URL}/docs", wait_until="domcontentloaded",
                           timeout=20000)
            live_page.wait_for_selector(".swagger-ui .opblock", timeout=8000)
            live_page.wait_for_timeout(1000)
            live_page.screenshot(path=str(SHOTS_DIR / "swagger-docs.png"),
                                  full_page=True)
            captured = True
            print("  captured swagger-docs.png (live /docs)")
        except Exception:
            pass
        finally:
            live_page.close()

        if not captured:
            offline_page = context.new_page()
            try:
                swagger_page = PAGES_DIR / "swagger.html"
                swagger_page.write_text(build_offline_swagger_html(),
                                        encoding="utf-8")
                offline_page.goto(swagger_page.as_uri(), wait_until="load")
                offline_page.wait_for_selector(".swagger-ui .opblock", timeout=20000)
                offline_page.wait_for_timeout(1200)
                offline_page.screenshot(path=str(SHOTS_DIR / "swagger-docs.png"),
                                        full_page=True)
                captured = True
                print("  captured swagger-docs.png (offline spec)")
            except Exception as exc:  # noqa: BLE001
                print(f"  WARNING: swagger-docs.png capture failed: {exc}")
            finally:
                offline_page.close()

        context.close()
        browser.close()


def _run_capture() -> None:
    """Wait for the server, collect interactions, and capture screenshots."""
    wait_for_health()
    print("App is healthy. Collecting API interactions ...", flush=True)
    interactions = collect_interactions()
    print("Capturing screenshots ...", flush=True)
    capture(interactions)


def main() -> None:
    SHOTS_DIR.mkdir(parents=True, exist_ok=True)
    if PAGES_DIR.exists():
        shutil.rmtree(PAGES_DIR)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    # When SCREENSHOT_USE_RUNNING_SERVER is set, assume the app is already
    # running at BASE_URL and only run the capture. Otherwise manage the server
    # lifecycle here.
    if os.environ.get("SCREENSHOT_USE_RUNNING_SERVER"):
        print(f"Using already-running server at {BASE_URL} ...", flush=True)
        _run_capture()
    else:
        if TEMP_DB.exists():
            TEMP_DB.unlink()
        env = dict(os.environ)
        env["DATABASE_URL"] = f"sqlite:///{TEMP_DB}"

        print("Starting FastAPI app on 127.0.0.1:8000 ...", flush=True)
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"],
            cwd=str(ROOT),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            _run_capture()
        finally:
            print("Stopping server ...", flush=True)
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
            if TEMP_DB.exists():
                TEMP_DB.unlink()

    pngs = sorted(SHOTS_DIR.glob("*.png"))
    print(f"\nDone. {len(pngs)} screenshot(s) in {SHOTS_DIR.relative_to(ROOT)}:", flush=True)
    for png in pngs:
        print(f"  - {png.name}", flush=True)


if __name__ == "__main__":
    main()
