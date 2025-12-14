"""
Builder introspection utilities.

Provides functions to extract builder method information for dynamic GUI generation.
"""

import inspect
from typing import List, Dict, Any, Optional, get_type_hints
from dataclasses import dataclass


@dataclass
class BuilderParam:
    """Represents a parameter of a builder method."""
    name: str
    param_type: str
    default: Any
    description: str
    

@dataclass
class BuilderMethod:
    """Represents a builder method with its metadata."""
    name: str
    description: str
    workflow_effect: str
    params: List[BuilderParam]
    category: str  # e.g., "Prompt", "Sampler", "Image", "Model", "SVG", "API"


def extract_workflow_effect(docstring: str) -> str:
    """Extract the 'Workflow Effect' section from a docstring."""
    if not docstring:
        return ""
    
    lines = docstring.split('\n')
    in_workflow_effect = False
    effect_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Workflow Effect:"):
            in_workflow_effect = True
            continue
        elif in_workflow_effect:
            if stripped.startswith("Args:") or stripped.startswith("Returns:"):
                break
            if stripped:
                effect_lines.append(stripped)
    
    return ' '.join(effect_lines)


def extract_description(docstring: str) -> str:
    """Extract the main description (first paragraph) from a docstring."""
    if not docstring:
        return ""
    
    lines = docstring.strip().split('\n')
    desc_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            break
        if stripped.startswith("Workflow Effect:") or stripped.startswith("Args:"):
            break
        desc_lines.append(stripped)
    
    return ' '.join(desc_lines)


def get_category_from_docstring(docstring: str, method_name: str) -> str:
    """Determine the category of a method based on docstring or method name."""
    docstring_lower = (docstring or "").lower()
    method_lower = method_name.lower()
    
    if any(word in method_lower for word in ['prompt', 'subject', 'negative', 'character', 'artist']):
        return "Prompt"
    elif any(word in method_lower for word in ['seed', 'steps', 'cfg', 'sampler', 'scheduler', 'denoise']):
        return "Sampler"
    elif any(word in method_lower for word in ['size', 'width', 'height', 'batch']):
        return "Image"
    elif any(word in method_lower for word in ['checkpoint', 'lora', 'model']):
        return "Model"
    elif any(word in method_lower for word in ['potracer', 'svg', 'output', 'prefix']):
        return "SVG"
    elif any(word in method_lower for word in ['url']):
        return "API"
    else:
        return "Other"


def get_builder_methods(builder_class) -> List[BuilderMethod]:
    """
    Extract all configurable methods from a builder class.
    
    Returns methods that:
    - Are public (don't start with _)
    - Return self (builder pattern)
    - Are not build/queue/reset/to_dict/to_json/save
    """
    excluded_methods = {'build', 'queue', 'reset', 'to_dict', 'to_json', 'save', 'random_seed'}
    methods = []
    
    for name, method in inspect.getmembers(builder_class, predicate=inspect.isfunction):
        if name.startswith('_') or name in excluded_methods:
            continue
        
        docstring = inspect.getdoc(method) or ""
        
        sig = inspect.signature(method)
        
        params = []
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            param_type = "str"
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "int"
                elif param.annotation == float:
                    param_type = "float"
                elif param.annotation == bool:
                    param_type = "bool"
                elif hasattr(param.annotation, '__origin__'):
                    param_type = str(param.annotation)
                else:
                    param_type = str(param.annotation.__name__) if hasattr(param.annotation, '__name__') else "str"
            
            default = None if param.default == inspect.Parameter.empty else param.default
            
            param_desc = ""
            if docstring:
                lines = docstring.split('\n')
                in_args = False
                for line in lines:
                    if line.strip().startswith("Args:"):
                        in_args = True
                        continue
                    if in_args:
                        if line.strip().startswith("Returns:"):
                            break
                        if line.strip().startswith(f"{param_name}:"):
                            param_desc = line.strip().split(":", 1)[1].strip()
                            break
            
            params.append(BuilderParam(
                name=param_name,
                param_type=param_type,
                default=default,
                description=param_desc
            ))
        
        if not params:
            continue
        
        methods.append(BuilderMethod(
            name=name,
            description=extract_description(docstring),
            workflow_effect=extract_workflow_effect(docstring),
            params=params,
            category=get_category_from_docstring(docstring, name)
        ))
    
    category_order = ["Prompt", "Sampler", "Image", "Model", "SVG", "API", "Other"]
    methods.sort(key=lambda m: (category_order.index(m.category) if m.category in category_order else 99, m.name))
    
    return methods


def get_builder_methods_by_category(builder_class) -> Dict[str, List[BuilderMethod]]:
    """Get builder methods organized by category."""
    methods = get_builder_methods(builder_class)
    by_category = {}
    
    for method in methods:
        if method.category not in by_category:
            by_category[method.category] = []
        by_category[method.category].append(method)
    
    return by_category
