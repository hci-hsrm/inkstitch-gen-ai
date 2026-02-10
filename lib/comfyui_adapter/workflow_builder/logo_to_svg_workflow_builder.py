#!/usr/bin/env python3
"""
Logo to SVG workflow builder using ComfyUI.
"""

from __future__ import annotations
from pathlib import Path

from ...utils.paths import get_resource_dir
from .base_workflow_builder import ComfyUiToSVGWorkflowBuilder


class LogoToSVGWorkflowBuilder(ComfyUiToSVGWorkflowBuilder):
    """
    Builder for the logo to SVG workflow.
    
    Uses a fluent interface pattern - all setter methods return self,
    allowing method chaining.
    """
    
    DEFAULT_WORKFLOW_PATH = Path(get_resource_dir("lib/comfyui_adapter/api_workflows")) / "logo_to_svg_workflow.json"