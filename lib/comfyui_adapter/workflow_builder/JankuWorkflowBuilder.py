#!/usr/bin/env python3
"""
Fluent builder pattern for JANKU anime/illustration workflow.
"""

from __future__ import annotations
import json
import copy
import random
import urllib.request
import urllib.error
import time
from pathlib import Path
from typing import Optional, Union


class JankuWorkflowBuilder:
    """
    Builder for the JANKU anime/illustration workflow.
    
    JANKU is a trained checkpoint based on NoobAI + RouWei Illustrious XL.
    Optimized for anime-style illustrations with good anatomy and prompt following.
    
    Uses a fluent interface pattern - all setter methods return self,
    allowing method chaining.
    """
    
    # Node IDs in the workflow
    NODE_CHECKPOINT = "1"
    NODE_POSITIVE_PROMPT = "3"
    NODE_NEGATIVE_PROMPT = "4"
    NODE_LATENT = "5"
    NODE_SAMPLER = "6"
    NODE_VAE_DECODE = "7"
    NODE_SAVE_IMAGE = "8"
    
    def __init__(self, workflow_path: Optional[Union[str, Path]] = None):
        """
        Initialize the workflow builder.
        
        Args:
            workflow_path: Path to workflow JSON. If None, uses the default
                          janku_workflow.json in the api-workflows directory.
        """
        if workflow_path is None:
            workflow_path = Path(__file__).parent.parent / "api_workflows" / "janku_workflow.json"
        
        with open(workflow_path, 'r') as f:
            self._template = json.load(f)
        
        self._workflow = copy.deepcopy(self._template)
        
        # Default values
        self._seed_value: Optional[int] = None
        self._comfyui_url = "http://127.0.0.1:8188"
    
    # -------------------------------------------------------------------------
    # Prompt Configuration
    # -------------------------------------------------------------------------
    
    def prompt(self, text: str) -> JankuWorkflowBuilder:
        """
        Set the positive prompt.
        
        Workflow Effect:
            Sets CLIPTextEncode node (node 3) text input.
            Use danbooru-style tags for best results. Include quality tags like
            "masterpiece, best quality" and character/scene descriptors.
        
        Args:
            text: Positive prompt with danbooru-style tags
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_POSITIVE_PROMPT]["inputs"]["text"] = text
        return self
    
    def negative_prompt(self, text: str) -> JankuWorkflowBuilder:
        """
        Set the negative prompt.
        
        Workflow Effect:
            Sets CLIPTextEncode node (node 4) text input.
            Default includes quality and anatomy negative tags.
            Add "nsfw" to negative to keep output SFW.
        
        Args:
            text: Negative prompt describing what to avoid
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_NEGATIVE_PROMPT]["inputs"]["text"] = text
        return self
    
    # -------------------------------------------------------------------------
    # Sampler Configuration
    # -------------------------------------------------------------------------
    
    def seed(self, value: int) -> JankuWorkflowBuilder:
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
    
    def random_seed(self) -> JankuWorkflowBuilder:
        """
        Use a random seed (default behavior).
        
        Workflow Effect:
            A random seed will be generated at build() time.
            Each queue() will produce a unique result.
        
        Returns:
            self for method chaining
        """
        self._seed_value = None
        return self
    
    def steps(self, count: int) -> JankuWorkflowBuilder:
        """
        Set the number of sampling steps.
        
        Workflow Effect:
            JANKU recommends 25-30 steps. More steps = higher quality but slower.
            Diminishing returns above 40.
        
        Args:
            count: Number of steps (recommended 25-30)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["steps"] = count
        return self
    
    def cfg(self, value: float) -> JankuWorkflowBuilder:
        """
        Set the CFG (classifier-free guidance) scale.
        
        Workflow Effect:
            JANKU recommends CFG 3-5 (lower than typical SDXL).
            Higher = stricter prompt adherence.
            5.0 is default for this workflow.
        
        Args:
            value: CFG value (recommended 3-5)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["cfg"] = value
        return self
    
    def sampler(self, name: str) -> JankuWorkflowBuilder:
        """
        Set the sampler algorithm.
        
        Workflow Effect:
            JANKU recommends "euler" or "euler_ancestral".
            Different samplers produce different aesthetics.
        
        Args:
            name: Sampler name (euler, euler_ancestral, dpmpp_2m, etc.)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["sampler_name"] = name
        return self
    
    def scheduler(self, name: str) -> JankuWorkflowBuilder:
        """
        Set the scheduler.
        
        Workflow Effect:
            JANKU recommends "normal" or "simple".
            Controls the noise schedule during denoising.
        
        Args:
            name: Scheduler name (normal, simple, karras, sgm_uniform)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["scheduler"] = name
        return self
    
    def denoise(self, value: float) -> JankuWorkflowBuilder:
        """
        Set the denoise strength.
        
        Workflow Effect:
            1.0 = full generation from noise (text-to-image).
            Lower values preserve more of input image (for img2img).
            Keep at 1.0 for this txt2img workflow.
        
        Args:
            value: Denoise value (0.0 to 1.0)
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAMPLER]["inputs"]["denoise"] = value
        return self
    
    # -------------------------------------------------------------------------
    # Image Configuration
    # -------------------------------------------------------------------------
    
    def size(self, width: int, height: int) -> JankuWorkflowBuilder:
        """
        Set the output image size.
        
        Workflow Effect:
            JANKU works best at resolutions like:
            - 1024x1536 (portrait, recommended)
            - 768x1344, 832x1216, 768x1280, 704x1408
            - 1536x1536 (stable without upscaling)
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_LATENT]["inputs"]["width"] = width
        self._workflow[self.NODE_LATENT]["inputs"]["height"] = height
        return self
    
    def portrait(self) -> JankuWorkflowBuilder:
        """
        Use portrait orientation (1024x1536).
        
        Workflow Effect:
            Sets size to JANKU's recommended portrait resolution.
        
        Returns:
            self for method chaining
        """
        return self.size(1024, 1536)
    
    def landscape(self) -> JankuWorkflowBuilder:
        """
        Use landscape orientation (1536x1024).
        
        Workflow Effect:
            Sets size to landscape resolution.
        
        Returns:
            self for method chaining
        """
        return self.size(1536, 1024)
    
    def square(self) -> JankuWorkflowBuilder:
        """
        Use square format (1024x1024).
        
        Workflow Effect:
            Sets size to square resolution.
        
        Returns:
            self for method chaining
        """
        return self.size(1024, 1024)
    
    def batch_size(self, count: int) -> JankuWorkflowBuilder:
        """
        Set how many images to generate at once.
        
        Workflow Effect:
            Generates multiple images in parallel (VRAM permitting).
            Each will be saved as a separate file.
        
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
    
    def checkpoint(self, name: str) -> JankuWorkflowBuilder:
        """
        Set the model checkpoint.
        
        Workflow Effect:
            Default is JANKU_v6.0.safetensors.
            VAE is baked in, no need for separate VAE loader.
        
        Args:
            name: Checkpoint filename
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_CHECKPOINT]["inputs"]["ckpt_name"] = name
        return self
    
    # -------------------------------------------------------------------------
    # Output Configuration
    # -------------------------------------------------------------------------
    
    def output_prefix(self, prefix: str) -> JankuWorkflowBuilder:
        """
        Set the output filename prefix.
        
        Workflow Effect:
            Output files will be named: {prefix}_{number}.png
            Saved to ComfyUI's output directory.
        
        Args:
            prefix: Filename prefix (e.g., "JANKU")
        
        Returns:
            self for method chaining
        """
        self._workflow[self.NODE_SAVE_IMAGE]["inputs"]["filename_prefix"] = prefix
        return self
    
    # -------------------------------------------------------------------------
    # API Configuration
    # -------------------------------------------------------------------------
    
    def url(self, comfyui_url: str) -> JankuWorkflowBuilder:
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
    
    def build(self) -> JankuWorkflowBuilder:
        """
        Finalize the workflow configuration.
        
        Sets the seed. Call this before queue() or to_dict().
        
        Returns:
            self for method chaining
        """
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
    
    def save(self, path: str) -> JankuWorkflowBuilder:
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
    
    def reset(self) -> JankuWorkflowBuilder:
        """
        Reset the workflow to the original template.
        
        Returns:
            self for method chaining
        """
        self._workflow = copy.deepcopy(self._template)
        self._seed_value = None
        return self


# -----------------------------------------------------------------------------
# Example usage
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate anime illustration using JANKU checkpoint")
    parser.add_argument("prompt", nargs="?", default="", help="Positive prompt")
    parser.add_argument("--negative", default="lowres, bad anatomy, bad hands, text, error, missing fingers, worst quality, low quality, jpeg artifacts, signature, watermark, blurry", help="Negative prompt")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--steps", type=int, default=30, help="Sampling steps")
    parser.add_argument("--cfg", type=float, default=5.0, help="CFG scale")
    parser.add_argument("--portrait", action="store_true", help="Use portrait orientation (1024x1536)")
    parser.add_argument("--landscape", action="store_true", help="Use landscape orientation (1536x1024)")
    parser.add_argument("--url", default="http://127.0.0.1:8188", help="ComfyUI URL")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for completion")
    
    args = parser.parse_args()
    
    workflow: JankuWorkflowBuilder = (
        JankuWorkflowBuilder()
        .prompt(args.prompt)
        .negative_prompt(args.negative)
        .steps(args.steps)
        .cfg(args.cfg)
        .url(args.url)
        .batch_size(1)
    )
    
    if args.portrait:
        workflow.portrait()
    elif args.landscape:
        workflow.landscape()
    
    if args.seed:
        workflow.seed(args.seed)
    
    workflow.build()
    
    print(f"Prompt: {args.prompt[:50]}...")
    print(f"Sending to ComfyUI at {args.url}...")
    
    try:
        result = workflow.queue(wait=not args.no_wait)
        
        if args.no_wait:
            print(f"Queued with prompt_id: {result['prompt_id']}")
        else:
            outputs = result.get("outputs", {})
            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    for img in node_output["images"]:
                        print(f"Image: {img['filename']}")
            print("Done!")
            
    except urllib.error.URLError:
        print(f"Cannot connect to ComfyUI at {args.url}")
        print("Make sure ComfyUI is running!")
        exit(1)
