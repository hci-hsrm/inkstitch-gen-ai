#!/usr/bin/env python3
"""
Fluent builder pattern for ComfyUI workflows.
"""

from __future__ import annotations
import json
import copy
import random
import urllib.request
import urllib.error
import time
from pathlib import Path
from typing import Optional, Literal, Union


class ContinuousLineToSVGWorkflowBuilder:
    """
    Builder for the continuous line drawing to SVG workflow.
    
    Uses a fluent interface pattern - all setter methods return self,
    allowing method chaining.
    """
    
    # Node IDs in the workflow
    NODE_CHECKPOINT = "1"
    NODE_LORA = "2"
    NODE_POSITIVE_PROMPT = "3"
    NODE_NEGATIVE_PROMPT = "4"
    NODE_LATENT = "5"
    NODE_SAMPLER = "6"
    NODE_VAE_DECODE = "7"
    NODE_POTRACER = "17"
    NODE_SAVE_SVG = "21"
    
    def __init__(self, workflow_path: Optional[Union[str, Path]] = None):
        """
        Initialize the workflow builder.
        
        Args:
            workflow_path: Path to workflow JSON. If None, uses the default
                          continuous_line_to_svg_workflow.json in the api-workflows directory.
        """
        if workflow_path is None:
            workflow_path = Path(__file__).parent.parent / "api_workflows" / "continuous_line_to_svg_workflow.json"
        
        with open(workflow_path, 'r') as f:
            self._template = json.load(f)
        
        self._workflow = copy.deepcopy(self._template)
        
        # Default values
        self._subject_text = "a cat"
        self._seed_value: Optional[int] = None
        self._comfyui_url = "http://127.0.0.1:8188"
    
    # -------------------------------------------------------------------------
    # Prompt Configuration
    # -------------------------------------------------------------------------
    
    def subject(self, text: str) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the subject to draw.
        
        Workflow Effect:
            "continuous line drawing, {subject}, single unbroken line, minimalist art..."
            This is the main content that will be drawn as a continuous line.
        
        Args:
            text: What to draw, e.g., "a cat sitting", "a person dancing"
        
        Returns:
            self for method chaining
        """
        self._subject_text = text
        return self
    
    def negative_prompt(self, text_g: str, text_l: Optional[str] = None) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the negative prompt.
        
        Workflow Effect:
            Tells the model what to avoid generating. Default includes: "ugly, blurry,
            multiple lines, shading, color, filled shapes" to keep output as clean line art.
        
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
    
    def seed(self, value: int) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the random seed for reproducibility.
        
        Workflow Effect:
            Same seed + same settings = identical output. Useful for reproducing
            or iterating on a specific generation.
        
        Args:
            value: Seed value (0 to 2^32-1)
        
        Returns:
            self for method chaining
        """
        self._seed_value = value
        return self
    
    def random_seed(self) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Use a random seed (default behavior).
        
        Workflow Effect:
            A random seed will be generated at build() time and set on the KSampler.
            Each queue() will produce a unique result.
        
        Returns:
            self for method chaining
        """
        self._seed_value = None
        return self
    
    def _steps(self, count: int) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the number of sampling steps.
        
        Workflow Effect:
            More steps = higher quality but slower. For continuous line art,
            25-30 steps usually sufficient. Diminishing returns above 50.
        
        Args:
            count: Number of steps (typically 20-50)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["steps"] = count
        return self
    
    def _cfg(self, value: float) -> ContinuousLineToSVGWorkflowBuilder:
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
    
    def _sampler(self, name: str) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the sampler algorithm.
        
        Workflow Effect:
            Different samplers produce different aesthetics. "euler" is fast and
            reliable for line art. "dpmpp_2m" often gives sharper results.
        
        Args:
            name: Sampler name (euler, euler_ancestral, dpm_2, dpm_2_ancestral, 
                  heun, dpm_fast, dpm_adaptive, lms, dpmpp_2s_ancestral,
                  dpmpp_sde, dpmpp_2m, etc.)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["sampler_name"] = name
        return self
    
    def _scheduler(self, name: str) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the scheduler.
        
        Workflow Effect:
            Controls the noise schedule during denoising. "normal" is standard,
            "karras" often produces cleaner results with fewer steps.
        
        Args:
            name: Scheduler name (normal, karras, exponential, sgm_uniform, simple)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["scheduler"] = name
        return self
    
    def _denoise(self, value: float) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the denoise strength.
        
        Workflow Effect:
            1.0 = full generation from noise (text-to-image).
            Lower values preserve more of input image (for img2img workflows).
            For this workflow, keep at 1.0.
        
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
    
    def _size(self, width: int, height: int) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the output image size.
        
        Workflow Effect:
            width/height/target dimensions. SDXL works best at 1024x1024
            or similar total pixel counts. The SVG output will trace this raster size.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
        
        Returns:
            self for method chaining
        """
        # Update latent size
        self._workflow[self.NODE_LATENT]["inputs"]["width"] = width
        self._workflow[self.NODE_LATENT]["inputs"]["height"] = height
        
        # Update SDXL prompt conditioning size
        for node_id in [self.NODE_POSITIVE_PROMPT, self.NODE_NEGATIVE_PROMPT]:
            self._workflow[node_id]["inputs"]["width"] = width
            self._workflow[node_id]["inputs"]["height"] = height
            self._workflow[node_id]["inputs"]["target_width"] = width
            self._workflow[node_id]["inputs"]["target_height"] = height
        
        return self
    
    def _batch_size(self, count: int) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set how many images to generate at once.
        
        Workflow Effect:
            Generates multiple images in parallel (VRAM permitting).
            Each will be converted to a separate SVG file.
        
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
    
    def _checkpoint(self, name: str) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the base model checkpoint.
        
        Workflow Effect:
            This is the base SDXL model. The LoRA is applied on top of this.
            Must be an SDXL-compatible checkpoint for best results.
        
        Args:
            name: Checkpoint filename (e.g., "sd_xl_base_1.0.safetensors")
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_CHECKPOINT]["inputs"]["ckpt_name"] = name
        return self
    
    def _lora(self, name: str) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the LoRA model.
        
        Workflow Effect:
            The ContinuousLineXL LoRA fine-tunes the model to produce single
            unbroken line drawings. This is what makes the continuous line style work.
        
        Args:
            name: LoRA filename (e.g., "ContinuousLineXL.safetensors")
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_LORA]["inputs"]["lora_name"] = name
        return self
    
    def lora_strength(self, model: float, clip: Optional[float] = None) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the LoRA strength.
        
        Workflow Effect:
            Higher = stronger continuous line effect. 1.0 is full strength.
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
        self,
        threshold: int = 128,
        turdsize: int = 2,
        corner_threshold: float = 1.0,
        opttolerance: float = 0.2
    ) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Configure Potracer SVG conversion settings.
        
        Workflow Effect:
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
    
    def _output_prefix(self, prefix: str) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the SVG output filename prefix.
        
        Workflow Effect:
            Output files will be named: {prefix}_{timestamp}.svg
            Saved to ComfyUI's output directory.
        
        Args:
            prefix: Filename prefix (e.g., "ContinuousLine")
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAVE_SVG]["inputs"]["filename_prefix"] = prefix
        return self
    
    # -------------------------------------------------------------------------
    # API Configuration
    # -------------------------------------------------------------------------
    
    def _url(self, comfyui_url: str) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Set the ComfyUI server URL.
        
        Workflow Effect:
            Does not modify the workflow JSON. Sets the target server for queue().
            Use this if ComfyUI is running on a different host or port.
        
        Args:
            comfyui_url: Server URL (e.g., "http://127.0.0.1:8188")
        
        Returns:
            self for method chaining
        """
        self._comfyui_url = comfyui_url
        return self
    
    # -------------------------------------------------------------------------
    # Build & Execute
    # -------------------------------------------------------------------------
    
    def build(self) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Finalize the workflow configuration.
        
        This applies the subject to the prompt template and sets the seed.
        Call this before queue() or to_dict().
        
        Returns:
            self for method chaining
        """
        # Build positive prompt from subject
        positive_g = f"continuous line drawing, {self._subject_text}, single unbroken line, minimalist art, black line on white background, elegant curves, simple"
        positive_l = "continuous line drawing, single unbroken line, minimalist art, black line on white background"
        
        self._workflow[self.NODE_POSITIVE_PROMPT]["inputs"]["text_g"] = positive_g
        self._workflow[self.NODE_POSITIVE_PROMPT]["inputs"]["text_l"] = positive_l
        
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
    
    def save(self, path: str) -> ContinuousLineToSVGWorkflowBuilder:
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
        # Queue the prompt
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
    
    def reset(self) -> ContinuousLineToSVGWorkflowBuilder:
        """
        Reset the workflow to the original template.
        
        Returns:
            self for method chaining
        """
        self._workflow = copy.deepcopy(self._template)
        self._subject_text = "a cat"
        self._seed_value = None
        return self