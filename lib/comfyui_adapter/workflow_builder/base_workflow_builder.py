#!/usr/bin/env python3
"""
Base class for ComfyUI to SVG workflow builders.
"""

from __future__ import annotations
import json
import copy
import random
import urllib.request
import urllib.error
import time
from pathlib import Path
from typing import Optional, Union, TypeVar

T = TypeVar('T', bound='ComfyUiToSVGWorkflowBuilder')


class ComfyUiToSVGWorkflowBuilder:
    """
    Abstract base class for ComfyUI to SVG workflow builders.
    
    Uses a fluent interface pattern - all setter methods return self,
    allowing method chaining.
    
    Subclasses must define:
        - DEFAULT_WORKFLOW_PATH: Class attribute with the path to the default workflow JSON
    
    Subclasses may override:
        - _build_prompt(): Build the positive prompt from the subject
    """
    
    # Subclasses must define this
    DEFAULT_WORKFLOW_PATH: Optional[Path] = None
    
    # Node IDs in the workflow (can be overridden by subclasses)
    NODE_CHECKPOINT = "1"
    NODE_LORA = "2"
    NODE_POSITIVE_PROMPT = "3"
    NODE_NEGATIVE_PROMPT = "4"
    NODE_LATENT = "5"
    NODE_SAMPLER = "6"
    NODE_VAE_DECODE = "7"
    NODE_POTRACER = "17"
    NODE_SAVE_SVG = "21"
    
    def __init__(self: T, workflow_path: Optional[Union[str, Path]] = None):
        """
        Initialize the workflow builder.
        
        Args:
            workflow_path: Path to workflow JSON. If None, uses DEFAULT_WORKFLOW_PATH.
        """
        if workflow_path is None:
            workflow_path = self.DEFAULT_WORKFLOW_PATH
        
        if workflow_path is None:
            raise ValueError(f"{self.__class__.__name__} must define DEFAULT_WORKFLOW_PATH")
        
        with open(workflow_path, 'r') as f:
            self._template = json.load(f)
        
        self._workflow = copy.deepcopy(self._template)
        
        # Default values
        self._subject_text = "a cat"
        self._seed_value: Optional[int] = None
        self._comfyui_url = "http://127.0.0.1:8188"
    
    def _build_prompt(self) -> None:
        """Build the positive prompt from the subject. Override in subclasses."""
        self._workflow[self.NODE_POSITIVE_PROMPT]["inputs"]["text_g"] += f", motiv: {self._subject_text}"
        self._workflow[self.NODE_POSITIVE_PROMPT]["inputs"]["text_l"] += f", motiv: {self._subject_text}"
    
    # -------------------------------------------------------------------------
    # Prompt Configuration
    # -------------------------------------------------------------------------
    
    def subject(self: T, text: str) -> T:
        """
        Set the subject to draw.
        
        Args:
            text: What to draw, e.g., "a cat sitting", "a person dancing"
        
        Returns:
            self for method chaining
        """
        self._subject_text = text
        return self
    
    def negative_prompt(self: T, text_g: str, text_l: Optional[str] = None) -> T:
        """
        Set the negative prompt.
        
        Workflow Effect:
            Tells the model what to avoid generating. Keep empty to use default.
        
        Args:
            text_g: Global negative prompt
            text_l: Local negative prompt (defaults to text_g if not provided)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_NEGATIVE_PROMPT]["inputs"]["text_g"] = text_g
        self._workflow[self.NODE_NEGATIVE_PROMPT]["inputs"]["text_l"] = text_l or text_g
        return self
    
    # -------------------------------------------------------------------------
    # Sampler Configuration
    # -------------------------------------------------------------------------
    
    def seed(self: T, value: int) -> T:
        """
        Set the random seed for reproducibility.
        
        Args:
            value: Seed value (0 to 2^32-1)
        
        Returns:
            self for method chaining
        """
        self._seed_value = value
        return self
    
    def steps(self: T, count: int) -> T:
        """
        Set the number of sampling steps.
        More steps = higher quality but slower.
        
        Args:
            count: Number of steps (typically 20-50)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["steps"] = count
        return self
    
    def _cfg(self: T, value: float) -> T:
        """
        Set the CFG (classifier-free guidance) scale.
        
        Workflow Effect:
            Higher = stricter prompt adherence but may look artificial.
            Lower = more creative but may ignore prompt details.
            7.0 is default, good range is 5-10 for line art.
        
        Args:
            value: CFG value (typically 5-15)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["cfg"] = value
        return self
    
    def _sampler(self: T, name: str) -> T:
        """
        Set the sampler algorithm.
        
        Args:
            name: Sampler name (euler, euler_ancestral, dpm_2, dpm_2_ancestral, 
                  heun, dpm_fast, dpm_adaptive, lms, dpmpp_2s_ancestral,
                  dpmpp_sde, dpmpp_2m, etc.)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["sampler_name"] = name
        return self
    
    def _scheduler(self: T, name: str) -> T:
        """
        Set the scheduler.
        
        Args:
            name: Scheduler name (normal, karras, exponential, sgm_uniform, simple)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["scheduler"] = name
        return self
    
    def _denoise(self: T, value: float) -> T:
        """
        Set the denoise strength.
        1.0 = full generation from noise (text-to-image).
        
        Args:
            value: Denoise value (0.0 to 1.0, typically 1.0 for txt2img)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["denoise"] = value
        return self
    
    # -------------------------------------------------------------------------
    # Image Configuration
    # -------------------------------------------------------------------------
    
    def _size(self: T, width: int, height: int) -> T:
        """
        Set the output image size.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_LATENT]["inputs"]["width"] = width
        self._workflow[self.NODE_LATENT]["inputs"]["height"] = height
        
        for node_id in [self.NODE_POSITIVE_PROMPT, self.NODE_NEGATIVE_PROMPT]:
            self._workflow[node_id]["inputs"]["width"] = width
            self._workflow[node_id]["inputs"]["height"] = height
            self._workflow[node_id]["inputs"]["target_width"] = width
            self._workflow[node_id]["inputs"]["target_height"] = height
        
        return self
    
    def _batch_size(self: T, count: int) -> T:
        """
        Set how many images to generate at once.
        
        Args:
            count: Number of images per batch
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_LATENT]["inputs"]["batch_size"] = count
        return self
    
    # -------------------------------------------------------------------------
    # Model Configuration
    # -------------------------------------------------------------------------
    
    def _checkpoint(self: T, name: str) -> T:
        """
        Set the base model checkpoint.
        
        Args:
            name: Checkpoint filename (e.g., "sd_xl_base_1.0.safetensors")
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_CHECKPOINT]["inputs"]["ckpt_name"] = name
        return self
    
    def _lora(self: T, name: str) -> T:
        """
        Set the LoRA model.
        
        Args:
            name: LoRA filename (e.g., "LogoXL.safetensors")
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_LORA]["inputs"]["lora_name"] = name
        return self
    
    def lora_strength(self: T, model: float, clip: Optional[float] = None) -> T:
        """
        Set the LoRA strength.
        Higher = stronger effect. 1.0 is full strength.
        Lower values blend with base model style. Usually keep at 0.8-1.0.
        
        Args:
            model: Model strength (0.0 to 2.0, typically around 1.0)
            clip: CLIP strength (defaults to model strength if not provided)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_LORA]["inputs"]["strength_model"] = model
        self._workflow[self.NODE_LORA]["inputs"]["strength_clip"] = clip if clip is not None else model
        return self
    
    # -------------------------------------------------------------------------
    # SVG Configuration
    # -------------------------------------------------------------------------
    
    def _potracer_settings(
        self: T,
        threshold: int = 128,
        turdsize: int = 2,
        corner_threshold: float = 1.0,
        opttolerance: float = 0.2
    ) -> T:
        """
        Configure Potracer SVG conversion settings.
        Controls how the raster image is traced into vector paths:
        - threshold: Brightness cutoff for black vs white (128 = middle)
        - turdsize: Removes specks smaller than this (higher = cleaner)
        - corner_threshold: Sharper corners (lower = more angular)
        - opttolerance: Curve smoothing (higher = simpler paths)
        
        Args:
            threshold: Black/white threshold (0-255)
            turdsize: Despeckle threshold
            corner_threshold: Corner sharpness
            opttolerance: Curve optimization tolerance
        
        Returns:
            self for method chaining
        """
        inputs = self._workflow[self.NODE_POTRACER]["inputs"]
        inputs["threshold"] = threshold
        inputs["turdsize"] = turdsize
        inputs["corner_threshold"] = corner_threshold
        inputs["opttolerance"] = opttolerance
        return self
    
    def _output_prefix(self: T, prefix: str) -> T:
        """
        Set the SVG output filename prefix.
        
        Workflow Effect:
            Output files will be named: {prefix}_{timestamp}.svg
            Saved to ComfyUI's output directory.
        
        Args:
            prefix: Filename prefix (e.g., "Logo")
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAVE_SVG]["inputs"]["filename_prefix"] = prefix
        return self
    
    # -------------------------------------------------------------------------
    # Build & Execute
    # -------------------------------------------------------------------------
    
    def build(self: T) -> T:
        """
        Finalize the workflow configuration.
        
        This applies the subject to the prompt template and sets the seed.
        Call this before queue() or to_dict().
        
        Returns:
            self for method chaining
        """
        self._build_prompt()
        
        # Set seed
        seed = self._seed_value if self._seed_value is not None else random.randint(0, 2**32 - 1)
        self._workflow[self.NODE_SAMPLER]["inputs"]["seed"] = seed
        
        return self
    
    def to_dict(self) -> dict:
        """
        Get the workflow as a dictionary (API format).
        
        Returns:
            The workflow dictionary ready to send to /prompt endpoint
        """
        return copy.deepcopy(self._workflow)
    
    def to_json(self, indent: int = 2) -> str:
        """
        Get the workflow as a JSON string.
        
        Args:
            indent: JSON indentation (default 2)
        
        Returns:
            JSON string of the workflow
        """
        return json.dumps(self._workflow, indent=indent)
    
    def save(self: T, path: str) -> T:
        """
        Save the workflow to a JSON file.
        
        Args:
            path: Output file path
        
        Returns:
            self for method chaining
        """
        with open(path, 'w') as f:
            json.dump(self._workflow, f, indent=2)
        return self
    
    def queue(self, wait: bool = True, timeout: int = 300) -> dict:
        """
        Queue the workflow for execution on ComfyUI.
        
        Args:
            wait: If True, wait for completion
            timeout: Maximum seconds to wait (only if wait=True)
        
        Returns:
            If wait=True: Full history including outputs
            If wait=False: Just the queue response with prompt_id
        
        Raises:
            urllib.error.URLError: If cannot connect to ComfyUI
            TimeoutError: If execution doesn't complete in time
        """
        data = json.dumps({"prompt": self._workflow}).encode('utf-8')
        req = urllib.request.Request(
            f"{self._comfyui_url}/prompt",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read())
        
        if not wait:
            return result
        
        # Wait for completion
        prompt_id = result["prompt_id"]
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            with urllib.request.urlopen(f"{self._comfyui_url}/history/{prompt_id}") as response:
                history = json.loads(response.read())
            
            if prompt_id in history:
                status = history[prompt_id].get("status", {})
                if status.get("completed", False) or "outputs" in history[prompt_id]:
                    return history[prompt_id]
            
            time.sleep(0.5)
        
        raise TimeoutError(f"Prompt {prompt_id} did not complete within {timeout} seconds")
    
    def reset(self: T) -> T:
        """
        Reset the workflow to the original template.
        
        Returns:
            self for method chaining
        """
        self._workflow = copy.deepcopy(self._template)
        self._subject_text = "a cat"
        self._seed_value = None
        return self
