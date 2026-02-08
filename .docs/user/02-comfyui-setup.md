# ComfyUI Setup

The AI SVG Generator sends requests to a
[ComfyUI](https://github.com/comfyanonymous/ComfyUI) server.
This document covers installation, required models, and how to start the server.

---

## Installing ComfyUI

Follow the official instructions at
[github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI#installing).

---

## Required Models

Each workflow expects specific models to be present in ComfyUI's `models/`
directory. At a minimum:

| Model type | Example | Path in ComfyUI |
|---|---|---|
| SDXL Checkpoint | `sd_xl_base_1.0.safetensors` | `models/checkpoints/` |
| LoRA (per workflow) | `continuous_line_sdxl.safetensors` | `models/loras/sdxl/` |

> Check the workflow's JSON template in the repo
> (`lib/comfyui_adapter/api_workflows/`) for the exact model filenames.

---

## Required Custom Nodes

The SVG workflows use a **Potracer** node to convert raster images to vector
paths. Make sure the corresponding ComfyUI custom node package is installed
(check the ComfyUI Manager or install manually).

---

## Starting ComfyUI

```bash
cd /path/to/ComfyUI
python main.py --listen 0.0.0.0 --port 8188
```

Verify it is reachable by opening `http://localhost:8188` in a browser.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| *"Connection refused"* in the extension | ComfyUI is not running, or the URL/port is wrong. |
| Model not found errors in ComfyUI console | Download the required checkpoint / LoRA and place it in the correct `models/` sub-directory. |
| Potracer node missing | Install the custom node package via ComfyUI Manager or clone it into `custom_nodes/`. |
| Generation hangs indefinitely | Check the ComfyUI terminal for errors. A missing node or model usually stalls the queue. |
