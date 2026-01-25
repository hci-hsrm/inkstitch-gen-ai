#!/usr/bin/env python3
"""
Logo to SVG workflow builder using ComfyUI.
"""

from __future__ import annotations
from pathlib import Path

from .base_workflow_builder import ComfyUiToSVGWorkflowBuilder


class LogoToSVGWorkflowBuilder(ComfyUiToSVGWorkflowBuilder):
    """
    Builder for the logo to SVG workflow.
    
    Uses a fluent interface pattern - all setter methods return self,
    allowing method chaining.
    """
    
    DEFAULT_WORKFLOW_PATH = Path(__file__).parent.parent / "api_workflows" / "logo_to_svg_workflow.json"