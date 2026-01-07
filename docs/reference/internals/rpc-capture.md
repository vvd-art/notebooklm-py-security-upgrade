# RPC Capture Guide

**Status:** Active
**Last Updated:** 2026-01-07
**Purpose:** How to capture and reverse-engineer NotebookLM RPC calls

---

## Overview

NotebookLM uses Google's `batchexecute` RPC protocol. This guide explains how to capture and decode RPC calls for different use cases.

### Key Concepts

| Term | Description |
|------|-------------|
| **batchexecute** | Google's internal RPC protocol endpoint |
| **RPC ID** | 6-character identifier (e.g., `wXbhsf`, `s0tc2d`) |
| **f.req** | URL-encoded JSON payload |
| **at** | CSRF token (SNlM0e value) |
| **Anti-XSSI** | `)]}'` prefix on responses |

### Protocol Flow

```
1. Build request: [[[rpc_id, json_params, null, "generic"]]]
2. Encode to f.req parameter
3. POST to /_/LabsTailwindUi/data/batchexecute
4. Strip )]}' prefix from response
5. Parse chunked JSON, extract result
```

---

## Choose Your Approach

| If you are... | Use this approach |
|---------------|-------------------|
| **Reporting a bug** or doing quick investigation | [Manual Capture](#manual-capture-for-bug-reports) |
| **Building library features** or systematic capture | [Playwright Automation](#playwright-automation-for-developers) |
| **An LLM agent** discovering new methods | [LLM Discovery Workflow](#llm-discovery-workflow) |

---

## Manual Capture (For Bug Reports)

**Best for:** Quick investigation, bug reports, one-off captures

### Step 1: Setup DevTools

1. Open Chrome → Navigate to `https://notebooklm.google.com/`
2. Open DevTools (`F12` or `Cmd+Option+I`)
3. Go to **Network** tab
4. Configure:
   - [x] **Preserve log** (prevents clearing on navigation)
   - [x] **Disable cache** (ensures fresh requests)
5. Filter by: `batchexecute`

### Step 2: Capture One Action

**CRITICAL**: Perform ONE action at a time to isolate the exact RPC call.

```
1. Clear network log immediately before action
2. Perform the UI action (e.g., rename notebook)
3. Wait for request to complete (check status code 200)
4. DO NOT perform any other actions
```

### Step 3: Document the Request

From the batchexecute request:

**Headers Tab:**
- `rpcids` query parameter = RPC method ID

**Payload Tab:**
- `f.req` = URL-encoded payload (decode this)
- `at` = CSRF token

**Response Tab:**
- Starts with `)]}'\n` (anti-XSSI prefix)
- Followed by chunked JSON

### Step 4: Decode Payload

**Manual decode in browser console:**
```javascript
const encoded = "...";  // Paste f.req value
const decoded = decodeURIComponent(encoded);
const outer = JSON.parse(decoded);
console.log("RPC ID:", outer[0][0][0]);
console.log("Params:", JSON.parse(outer[0][0][1]));
```

**Include in bug report:**
- RPC ID (e.g., `wXbhsf`)
- Decoded params (JSON format)
- Error message or unexpected behavior
- Response if relevant

---

## Playwright Automation (For Developers)

**Best for:** Systematic RPC capture, building new features, CI/CD integration

### Setup

```python
from playwright.async_api import async_playwright
import json
import time
from urllib.parse import unquote

async def setup_capture_session():
    """Initialize Playwright with network interception."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch_persistent_context(
        user_data_dir="./browser_state",
        headless=False,
    )
    page = browser.pages[0] if browser.pages else await browser.new_page()

    # Storage for captured RPCs
    captured_rpcs = []

    # Intercept batchexecute requests
    async def handle_request(request):
        if "batchexecute" in request.url:
            post_data = request.post_data
            if post_data and "f.req" in post_data:
                # Use proper URL parsing (handles encoded & and = in values)
                from urllib.parse import parse_qs
                params = parse_qs(post_data)
                f_req = params.get("f.req", [None])[0]
                if f_req:
                    decoded = decode_f_req(f_req)
                    captured_rpcs.append({
                        "timestamp": time.time(),
                        "url": request.url,
                        "rpc_id": decoded["rpc_id"],
                        "params": decoded["params"],
                    })

    page.on("request", handle_request)
    return page, captured_rpcs


def decode_f_req(encoded: str) -> dict:
    """Decode f.req parameter to extract RPC details."""
    decoded = unquote(encoded)
    outer = json.loads(decoded)
    inner = outer[0][0]
    return {
        "rpc_id": inner[0],
        "params": json.loads(inner[1]),
        "raw": inner,
    }
```

### Triggering Actions

```python
async def trigger_action(page, captured_rpcs, action_type: str, **kwargs):
    """Trigger a specific UI action and return captured RPC."""
    captured_rpcs.clear()

    if action_type == "list_notebooks":
        await page.goto("https://notebooklm.google.com/")
        await page.wait_for_selector("mat-card", timeout=10000)

    elif action_type == "create_notebook":
        await page.click("button:has-text('Create new')")
        await page.wait_for_url("**/notebook/**", timeout=10000)

    elif action_type == "add_source_url":
        url = kwargs.get("url")
        await page.click("button:has-text('Add source')")
        await page.wait_for_selector("[role='dialog']", timeout=5000)
        await page.click("button:has-text('Website')")
        await page.fill("textarea[placeholder*='links']", url)
        await page.click("button:has-text('Insert')")
        await page.wait_for_timeout(5000)

    return list(captured_rpcs)
```

### Example Capture Session

```python
async def capture_new_method():
    """Example: Discover the RPC for a new action."""
    page, captured = await setup_capture_session()

    # Authenticate if needed
    await page.goto("https://notebooklm.google.com/")

    # Capture the action
    rpcs = await trigger_action(page, captured, "create_notebook")

    # Print results
    for rpc in rpcs:
        print(f"RPC ID: {rpc['rpc_id']}")
        print(f"Params: {json.dumps(rpc['params'], indent=2)}")

    await browser.close()
```

---

## LLM Discovery Workflow

**Best for:** AI agents discovering new RPC methods, adaptive exploration

### Context for LLM

When investigating NotebookLM RPC calls, use this context:

```
NotebookLM Protocol Facts:
- Endpoint: /_/LabsTailwindUi/data/batchexecute
- RPC IDs are 6-character strings (e.g., "wXbhsf")
- Payload is triple-nested: [[[rpc_id, json_params, null, "generic"]]]
- Response has )]}' anti-XSSI prefix
- Parameters are position-sensitive arrays

Source of Truth:
- Canonical RPC IDs: src/notebooklm/rpc/types.py
- Payload structures: docs/reference/internals/rpc-ui-reference.md
```

### Discovery Prompt Template

Use this when discovering a new RPC method:

```
Task: Discover the RPC call for [ACTION_NAME]

Steps:
1. Identify the UI element that triggers this action
2. Set up network interception for batchexecute
3. Trigger the UI action
4. Capture the RPC request

Document:
- RPC ID (6-character string)
- Payload structure with parameter positions
- Any source ID nesting patterns (single/double/triple)
- Response structure

Reference: See rpc-ui-reference.md for existing patterns to follow.
```

### Validation Workflow

After discovering a new RPC:

```python
async def validate_rpc_call(rpc_id: str, params: list, expected_action: str):
    """Validate an RPC call works correctly."""
    from notebooklm import NotebookLMClient

    async with await NotebookLMClient.from_storage() as client:
        result = await client._rpc_call(RPCMethod(rpc_id), params)

    assert result is not None, f"RPC {rpc_id} returned None"

    return {
        "rpc_id": rpc_id,
        "action": expected_action,
        "status": "verified",
        "timestamp": datetime.now().isoformat(),
    }
```

---

## Common Patterns

### Parameter Position Sensitivity

NotebookLM RPC calls are **position-sensitive** - parameters must be at exact array indices.

**Example: ADD_SOURCE (URL)**
```python
params = [
    [[None, None, None, None, None, None, None, [url], None, None, 1]],  # Position 0
    notebook_id,   # Position 1
    [2],           # Position 2
    [1, None, None, None, None, None, None, None, None, None, [1]],  # Position 3
]
```

### Source ID Nesting

Different methods require different nesting levels:

| Nesting | Example | Used By |
|---------|---------|---------|
| Single | `source_id` | Simple lookups |
| Double | `[[source_id]]` | DELETE_SOURCE, UPDATE_SOURCE |
| Triple | `[[[source_id]]]` | CREATE_ARTIFACT source lists |

### Response Parsing

```python
import json
import re

def parse_response(text: str, rpc_id: str):
    """Parse batchexecute response."""
    # Strip anti-XSSI prefix
    if text.startswith(")]}'"):
        text = re.sub(r"^\)\]\}'\r?\n", "", text)

    # Find wrb.fr chunk for our RPC ID
    for line in text.split("\n"):
        try:
            chunk = json.loads(line)
            if chunk[0] == "wrb.fr" and chunk[1] == rpc_id:
                result = chunk[2]
                return json.loads(result) if isinstance(result, str) else result
        except (json.JSONDecodeError, IndexError):
            continue
    return None
```

---

## Troubleshooting

### Request Returns Null (No Error)

**Cause:** Payload format is close but not exact.

**Fix:** Capture exact browser request and compare byte-by-byte:
```python
import json
your_params = [...]
captured_params = [...]
print(json.dumps(your_params, separators=(",", ":")))
print(json.dumps(captured_params, separators=(",", ":")))
```

### RPC ID Not Found in Response

**Cause:** Wrong RPC ID or different chunk format.

**Fix:** Log all chunks to find the result:
```python
for line in response.split("\n"):
    try:
        chunk = json.loads(line)
        print(f"Type: {chunk[0]}, ID: {chunk[1] if len(chunk) > 1 else 'N/A'}")
    except:
        continue
```

### CSRF Token Expired

**Symptoms:** 403 errors or authentication failures.

**Fix:** Re-fetch tokens via browser or refresh storage state:
```python
await client.refresh_auth()
```

---

## Adding New RPC Methods

See **[Adding RPC Methods Guide](../../contributing/adding-rpc-methods.md)** for the complete step-by-step workflow.

Quick summary:
1. Capture traffic using methodology above
2. Decode payload and identify parameter positions
3. Add to `rpc/types.py` and implement in `_*.py`
4. Test with unit, integration, and E2E tests
5. Document in `rpc-ui-reference.md`
