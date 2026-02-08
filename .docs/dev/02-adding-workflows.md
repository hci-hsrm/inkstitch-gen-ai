# Adding New AI Workflows

This guide walks you through every step required to add a brand-new
ComfyUI-backed workflow to the Ink/Stitch AI extension.

---

## Architecture at a Glance

```
lib/comfyui_adapter/
├── api_workflows/                   # raw ComfyUI API-format JSON files
│   ├── continuous_line_to_svg_workflow.json
│   └── logo_to_svg_workflow.json
├── workflow_builder/
│   ├── base_workflow_builder.py     # abstract fluent-builder base class
│   ├── continous_line_to_svg_workflow_builder.py
│   └── logo_to_svg_workflow_builder.py
├── builder_introspection.py         # reflection → auto-generated GUI controls
└── __init__.py                      # WORKFLOW_REGISTRY + helper functions
```

**Data flow:**

```
ComfyUI JSON template
       ↓
WorkflowBuilder (fluent setters)
       ↓  .build()
Configured JSON payload
       ↓  .queue()
HTTP POST to ComfyUI /prompt
       ↓
ComfyUI runs the graph → SVG files
       ↓
PreviewPanel fetches & displays results
```

---

## Step-by-Step: Add a New Workflow

### 1. Export the ComfyUI Workflow as API-Format JSON

In the ComfyUI web UI:

1. Build your node graph until it produces the output you want.
2. Open **Settings → Enable Dev mode options**.
3. Click **Save (API Format)** — this gives you the numbered-node JSON that
   the `/prompt` endpoint expects.
4. Save the file to:
   ```
   lib/comfyui_adapter/api_workflows/<your_workflow_name>_workflow.json
   ```

> **Tip:** Keep the node IDs stable. The builder class references them by
> their string ID (e.g. `"1"`, `"3"`, `"17"`).

---

### 2. Create a Workflow Builder Class

Create a new file in `lib/comfyui_adapter/workflow_builder/`:

```python
# lib/comfyui_adapter/workflow_builder/my_new_workflow_builder.py

#!/usr/bin/env python3
"""
My-new-thing to SVG workflow builder using ComfyUI.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from .base_workflow_builder import ComfyUiToSVGWorkflowBuilder


class MyNewWorkflowBuilder(ComfyUiToSVGWorkflowBuilder):
    """
    Builder for the my-new-thing to SVG workflow.

    Uses a fluent interface pattern — all setter methods return self,
    allowing method chaining.
    """

    # Point at the JSON you exported in step 1
    DEFAULT_WORKFLOW_PATH = (
        Path(__file__).parent.parent
        / "api_workflows"
        / "my_new_workflow.json"
    )

    # (Optional) Override node IDs if your graph uses different numbers
    # NODE_CHECKPOINT = "1"
    # NODE_POSITIVE_PROMPT = "3"

    # ------------------------------------------------------------------
    # Custom builder methods
    # ------------------------------------------------------------------

    def style_strength(self, value: float = 0.8) -> "MyNewWorkflowBuilder":
        """
        Adjust the stylistic strength of the LoRA.

        Workflow Effect:
            Higher values produce a stronger style but may reduce prompt
            adherence.

        Args:
            value: Strength from 0.0 to 2.0 (default 0.8)

        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_LORA]["inputs"]["strength_model"] = value
        return self
```

#### Rules for Builder Methods

| Rule | Why |
|---|---|
| Every public setter **must return `self`**. | Enables method chaining (`builder.subject("cat").steps(30).build()`). |
| Use **type annotations** on parameters. | The introspection system reads them to pick the right GUI widget (`int` → `SpinCtrl`, `float` → `SpinCtrlDouble`, `str` → `TextCtrl`, `bool` → `CheckBox`). |
| Provide a **default value** for every parameter. | Shown as the initial value in the auto-generated settings panel. |
| Write a **docstring** with `Workflow Effect:` and `Args:` sections. | The GUI uses these as tooltips. `builder_introspection.py` parses them. |
| Prefix truly internal methods or methodes you want to hide `_`. | They are excluded from the auto-generated GUI. |

---

### 3. Register the Builder

#### 3a. Export from the `workflow_builder` package

Edit `lib/comfyui_adapter/workflow_builder/__init__.py`:

```python
from .my_new_workflow_builder import MyNewWorkflowBuilder

__all__ = [
    "ComfyUiToSVGWorkflowBuilder",
    "ContinuousLineToSVGWorkflowBuilder",
    "LogoToSVGWorkflowBuilder",
    "MyNewWorkflowBuilder",           # new
]
```

#### 3b. Add to the registry in `lib/comfyui_adapter/__init__.py`

```python
from .workflow_builder import (
    ContinuousLineToSVGWorkflowBuilder,
    LogoToSVGWorkflowBuilder,
    MyNewWorkflowBuilder,              # new
)

WORKFLOW_REGISTRY = {
    "ContinuousLineToSVGWorkflowBuilder": ContinuousLineToSVGWorkflowBuilder,
    "LogoToSVGWorkflowBuilder": LogoToSVGWorkflowBuilder,
    "MyNewWorkflowBuilder": MyNewWorkflowBuilder,  # new
}

WORKFLOW_DISPLAY_NAMES = {
    "ContinuousLineToSVGWorkflowBuilder": "Continuous Line to SVG",
    "MyNewWorkflowBuilder": "My New Thing to SVG",  # new
}
```

That's it — the GUI picks up new registry entries automatically at startup.

---

### 4. (Optional) Override `_build_prompt()`

The base class appends the subject to the existing prompt template.
If your workflow needs a completely different prompt structure, override
`_build_prompt()`:

```python
def _build_prompt(self) -> None:
    """Build a custom prompt for this workflow."""
    self._workflow[self.NODE_POSITIVE_PROMPT]["inputs"]["text_g"] = (
        f"pixel art sprite of {self._subject_text}, 16-bit style"
    )
    self._workflow[self.NODE_POSITIVE_PROMPT]["inputs"]["text_l"] = (
        f"pixel art sprite of {self._subject_text}"
    )
```

---

## How the GUI Discovers Your Methods

`lib/comfyui_adapter/builder_introspection.py` uses Python's `inspect` module
to iterate over every **public, non-excluded** method of your builder class and
extract:

| Extracted info | Source |
|---|---|
| **Parameter name, type, default** | Method signature + type annotations |
| **Description / tooltip** | Docstring — first paragraph |
| **Workflow effect** | Docstring `Workflow Effect:` section |
| **Parameter description** | Docstring `Args:` section |
| **Category** | Inferred from the method name (keywords like `prompt`, `seed`, `model`, `svg`, …) |

The `SettingsPanel` calls `get_builder_methods_by_category(builder_class)` and
generates a `wx` control for each parameter. When the user clicks **Generate**,
`SettingsPanel.apply_to_builder(builder)` calls each method with the current
control value.

> **Key insight:** You never have to touch the GUI code. Just write well-typed,
> well-documented builder methods and the settings panel builds itself.

---