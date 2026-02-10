#!/usr/bin/env python3
"""
Continuous line to SVG workflow builder using ComfyUI.
"""

from __future__ import annotations
from pathlib import Path

from ...utils.paths import get_resource_dir
from .base_workflow_builder import ComfyUiToSVGWorkflowBuilder


class ContinuousLineToSVGWorkflowBuilder(ComfyUiToSVGWorkflowBuilder):
    """
    Builder for the continuous line drawing to SVG workflow.
    
    Uses a fluent interface pattern - all setter methods return self,
    allowing method chaining.
    """
    
    DEFAULT_WORKFLOW_PATH = Path(get_resource_dir("lib/comfyui_adapter/api_workflows")) / "continuous_line_to_svg_workflow.json"

    