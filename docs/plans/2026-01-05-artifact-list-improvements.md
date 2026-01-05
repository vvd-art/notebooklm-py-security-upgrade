# Artifact List Command Improvements

**Date:** 2026-01-05
**Status:** Design Approved

## Overview

Improve the `artifact list` command to match CLI conventions and provide more useful information.

## Current Issues

1. `artifact list` requires `notebook_id` as a positional argument, unlike all other commands which use `-n/--notebook` option with context fallback
2. Table doesn't display artifact type, even though the data is available
3. Creation time is not shown

## Design

### 1. Command Signature Change

**Current:**
```python
@artifact.command("list")
@click.argument("notebook_id")
@click.option("--type", ...)
def artifact_list(ctx, notebook_id, artifact_type):
```

**New:**
```python
@artifact.command("list")
@click.option("-n", "--notebook", "notebook_id", default=None,
              help="Notebook ID (uses current if not set)")
@click.option("--type", ...)
def artifact_list(ctx, notebook_id, artifact_type):
    nb_id = require_notebook(notebook_id)  # Fallback to context
```

**Usage Examples:**
- `notebooklm artifact list` - uses context
- `notebooklm artifact list -n nb_123` - explicit notebook
- `notebooklm artifact list --type video` - filter by type with context

### 2. Type Display Mapping

Map artifact type IDs to human-readable names with emojis:

```python
ARTIFACT_TYPE_DISPLAY = {
    1: "🎵 Audio Overview",
    2: "📄 Briefing Doc",
    3: "🎥 Video Overview",
    4: "📝 Quiz",           # Also used for flashcards
    5: "🧠 Mind Map",
    6: "📊 Report",
    7: "🖼️ Infographic",
    8: "🎞️ Slide Deck",
    9: "📋 Data Table",
}
```

### 3. Table Structure

**New Column Order:**
- ID (existing)
- Title (existing)
- **Type** (new)
- **Created** (new)
- Status (existing - moved to end)

**Implementation:**
```python
table = Table(title=f"Artifacts in {notebook_id}")
table.add_column("ID", style="cyan")
table.add_column("Title", style="green")
table.add_column("Type")
table.add_column("Created", style="dim")
table.add_column("Status", style="yellow")

for art in artifacts:
    if isinstance(art, list) and len(art) > 0:
        # Artifact structure: [id, title, type, ..., status, ..., created_at_list, ...]
        # Index 15 contains [seconds, nanoseconds] for creation time
        art_id = str(art[0] or "-")
        title = str(art[1] if len(art) > 1 else "-")
        type_id = art[2] if len(art) > 2 else None
        status_code = art[4] if len(art) > 4 else None
        created_at_list = art[15] if len(art) > 15 else None

        # Format type
        type_display = ARTIFACT_TYPE_DISPLAY.get(type_id, f"Unknown ({type_id})")

        # Format timestamp - extract seconds from [seconds, nanoseconds] list
        if created_at_list and isinstance(created_at_list, list) and len(created_at_list) > 0:
            created = datetime.fromtimestamp(created_at_list[0]).strftime("%Y-%m-%d %H:%M")
        else:
            created = "-"

        # Format status
        status = "completed" if status_code == 3 else "processing" if status_code == 1 else str(status_code)

        table.add_row(art_id, title, type_display, created, status)
```

### 4. Edge Cases

1. **Unknown type ID**: Display "Unknown (ID: X)" if type not in mapping
2. **Missing fields**: Use "-" for any missing data
3. **Filter behavior**: Type column still shows when using `--type` filter (confirms filter worked)
4. **Empty list**: Existing "No artifacts found" message remains

### 5. Example Output

```
Artifacts in nb_abc123
┌─────────┬─────────────────┬──────────────────────┬─────────────────┬───────────┐
│ ID      │ Title           │ Type                 │ Created         │ Status    │
├─────────┼─────────────────┼──────────────────────┼─────────────────┼───────────┤
│ art_123 │ Chapter 1       │ 🎵 Audio Overview    │ 2026-01-05 14:30│ completed │
│ art_124 │ Introduction    │ 🎥 Video Overview    │ 2026-01-05 15:15│ processing│
│ art_125 │ Summary Stats   │ 🖼️ Infographic      │ 2026-01-04 09:20│ completed │
└─────────┴─────────────────┴──────────────────────┴─────────────────┴───────────┘
```

## Implementation Notes

- Location: `src/notebooklm/notebooklm_cli.py` lines 899-958
- Add `ARTIFACT_TYPE_DISPLAY` constant near top of file or in `rpc/types.py`
- Import `datetime` if not already imported
- Ensure existing tests are updated for new signature
- Add new test cases for type display and timestamp formatting

## Benefits

1. **Consistency**: Matches command signature pattern used throughout CLI
2. **Usability**: Default context behavior reduces typing
3. **Information**: Type and creation time help identify and sort artifacts
4. **Visual**: Emojis make types instantly recognizable
