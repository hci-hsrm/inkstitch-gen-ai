"""
ComfyUI Adapter Module

Provides workflow builders and API integration for ComfyUI.
"""

from .workflow_builder import (
    JankuWorkflowBuilder,
    ContinuousLineToSVGWorkflowBuilder,
)

# Registry of available workflows - keyed by class name for introspection
WORKFLOW_REGISTRY = {
    "ContinuousLineToSVGWorkflowBuilder": ContinuousLineToSVGWorkflowBuilder,
    "JankuWorkflowBuilder": JankuWorkflowBuilder,
}

# Display names for workflows
WORKFLOW_DISPLAY_NAMES = {
    "ContinuousLineToSVGWorkflowBuilder": "Continuous Line to SVG",
    "JankuWorkflowBuilder": "Janku (Anime/Illustration)",
}

def get_available_workflows():
    """Return list of available workflow class names."""
    return list(WORKFLOW_REGISTRY.keys())

def get_workflow_builder(workflow_name: str):
    """Get a workflow builder class by name (returns the class, not an instance)."""
    if workflow_name not in WORKFLOW_REGISTRY:
        return None
    return WORKFLOW_REGISTRY[workflow_name]

def get_workflow_display_name(workflow_name: str):
    """Get the display name for a workflow."""
    return WORKFLOW_DISPLAY_NAMES.get(workflow_name, workflow_name)

__all__ = [
    "JankuWorkflowBuilder",
    "ContinuousLineToSVGWorkflowBuilder",
    "WORKFLOW_REGISTRY",
    "get_available_workflows",
    "get_workflow_builder",
    "get_workflow_display_name",
]
