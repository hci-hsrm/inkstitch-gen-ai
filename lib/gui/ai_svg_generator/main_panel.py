import wx
import threading
import sys

from ...i18n import _
from .settings_panel import SettingsPanel
from .adapter_panel import AdapterPanel
from .preview_panel import PreviewPanel


class AISVGGeneratorPanel(wx.Panel):
    """Main panel for the AI SVG Generator with split view."""

    def __init__(self, parent, **kwargs):
        self.extension = kwargs.pop("extension", None)
        super().__init__(parent, wx.ID_ANY)

        self.parent = parent
        self.generating = False

        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)

        self.left_panel = wx.Panel(self.splitter)
        left_sizer = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(self.left_panel, wx.ID_ANY)

        self.adapter_panel = AdapterPanel(self.notebook, on_workflow_changed=self._on_workflow_changed)
        
        initial_workflow = self.adapter_panel.get_workflow_name()
        self.settings_panel = SettingsPanel(self.notebook, workflow_name=initial_workflow)
        
        self.notebook.AddPage(self.settings_panel, _("Settings"))
        self.notebook.AddPage(self.adapter_panel, _("Adapter"))

        left_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

        self.generate_button = wx.Button(self.left_panel, label=_("Generate SVGs"))
        self.generate_button.Bind(wx.EVT_BUTTON, self.on_generate)
        left_sizer.Add(self.generate_button, 0, wx.EXPAND | wx.ALL, 10)
        
        self.status_text = wx.StaticText(self.left_panel, label="")
        left_sizer.Add(self.status_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.left_panel.SetSizer(left_sizer)

        self.preview_panel = PreviewPanel(self.splitter, extension=self.extension)

        self.splitter.SplitVertically(self.left_panel, self.preview_panel)
        self.splitter.SetMinimumPaneSize(300)
        self.splitter.SetSashPosition(400)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(main_sizer)
    
    def _on_workflow_changed(self, workflow_name):
        """Handle workflow selection change."""
        self.settings_panel.update_workflow(workflow_name)

    def on_generate(self, event):
        """Handle generate button click."""
        if self.generating:
            return
        
        try:
            builder = self.adapter_panel.get_workflow_builder()
            if not builder:
                wx.MessageBox(
                    _("Please select a workflow in the Adapter tab."),
                    _("AI SVG Generator"),
                    wx.OK | wx.ICON_WARNING
                )
                return
            
            server_url = self.adapter_panel.get_inference_url()
            
            self.settings_panel.apply_to_builder(builder)
            
            self.generating = True
            self.generate_button.Enable(False)
            self.status_text.SetLabel(_("Building workflow..."))
            self.status_text.SetForegroundColour(wx.Colour(0, 100, 0))
            self.Layout()
            
            print(f"Starting generation with workflow builder: {builder.__class__.__name__}", file=sys.stderr)
            print(f"Server URL: {server_url}", file=sys.stderr)
            
            thread = threading.Thread(target=self._run_generation, args=(builder,))
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            import traceback
            print(f"Error in on_generate: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            self._on_generation_error(str(e))
    
    def _run_generation(self, builder):
        """Run the generation process in a background thread."""
        import os
        debug_file = os.path.expanduser("~/ai_svg_debug.log")
        
        try:
            with open(debug_file, "w") as f:
                f.write("=== AI SVG Generator Debug Log ===\n")
                
                wx.CallAfter(self._update_status, _("Building workflow..."))
                builder.build()
                f.write("Workflow built successfully\n")
                
                wx.CallAfter(self._update_status, _("Sending to ComfyUI..."))
                f.write(f"Server URL: {builder._comfyui_url}\n")
                
                result = builder.queue(wait=True, timeout=300)
                
                outputs = result.get("outputs", {})
                f.write(f"\nOutputs keys: {list(outputs.keys())}\n")
                
                files = []
                
                for node_id, node_output in outputs.items():
                    f.write(f"\nNode {node_id}: {type(node_output).__name__}\n")
                    
                    if not node_output:
                        continue
                    
                    if isinstance(node_output, dict):
                        filename = None
                        
                        if "saved_svg" in node_output:
                            filename_list = node_output["saved_svg"]
                            if isinstance(filename_list, list):
                                filename = ''.join(filename_list)
                            else:
                                filename = str(filename_list)
                            f.write(f"Found saved_svg filename: {filename}\n")
                        
                        elif "path" in node_output:
                            path_list = node_output["path"]
                            if isinstance(path_list, list):
                                path = ''.join(path_list)
                            else:
                                path = str(path_list)
                            f.write(f"Found path: {path}\n")
                            filename = os.path.basename(path)
                            f.write(f"Extracted filename: {filename}\n")
                        
                        if filename:
                            for subfolder in ["", "output", "exp_data"]:
                                f.write(f"Trying to download {filename} from subfolder='{subfolder}'\n")
                                file_data = self._download_file(builder._comfyui_url, filename, subfolder, "output")
                                if file_data:
                                    f.write(f"Downloaded {len(file_data)} bytes from subfolder='{subfolder}'\n")
                                    files.append({
                                        'data': file_data,
                                        'filename': filename,
                                        'is_svg': filename.endswith('.svg')
                                    })
                                    break
                            else:
                                f.write(f"Failed to download {filename} from any subfolder\n")
                        
                        elif "images" in node_output:
                            for img in node_output["images"]:
                                filename = img.get("filename", f"output_{node_id}.png")
                                subfolder = img.get("subfolder", "")
                                f.write(f"Found image: {filename}\n")
                                file_data = self._download_file(builder._comfyui_url, filename, subfolder, "output")
                                if file_data:
                                    files.append({
                                        'data': file_data,
                                        'filename': filename,
                                        'is_svg': filename.endswith('.svg')
                                    })
                    
                    elif isinstance(node_output, str):
                        filename = node_output.strip()
                        if filename.endswith(('.svg', '.png', '.jpg', '.jpeg')):
                            f.write(f"Found file: {filename}\n")
                            file_data = self._download_file(builder._comfyui_url, filename, "exp_data", "output")
                            if file_data:
                                files.append({
                                    'data': file_data,
                                    'filename': filename,
                                    'is_svg': filename.endswith('.svg')
                                })
                
                f.write(f"\nTotal files found: {len(files)}\n")
                
            if files:
                wx.CallAfter(self._on_generation_success, files)
            else:
                error_msg = f"No output files found. Check ~/ai_svg_debug.log for details"
                wx.CallAfter(self._on_generation_error, error_msg)
                
        except Exception as e:
            import traceback
            with open(debug_file, "a") as f:
                f.write(f"\nException: {e}\n")
                traceback.print_exc(file=f)
            wx.CallAfter(self._on_generation_error, f"Error: {e}. Check ~/ai_svg_debug.log")
    
    def _download_file(self, base_url, filename, subfolder, file_type):
        """Download a file from ComfyUI server."""
        import urllib.request
        import urllib.parse
        
        try:
            params = urllib.parse.urlencode({
                'filename': filename,
                'subfolder': subfolder,
                'type': file_type
            })
            url = f"{base_url}/view?{params}"
            
            print(f"Downloading from: {url}", file=sys.stderr)
            
            with urllib.request.urlopen(url, timeout=30) as response:
                data = response.read()
                print(f"Downloaded {len(data)} bytes", file=sys.stderr)
                return data
        except Exception as e:
            print(f"Error downloading {filename}: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return None
    
    def _update_status(self, message):
        """Update status text (called from main thread)."""
        self.status_text.SetLabel(message)
        self.Layout()
    
    def _on_generation_success(self, files):
        """Handle successful generation (called from main thread)."""
        self.generating = False
        self.generate_button.Enable(True)
        self.status_text.SetLabel(_("Generation complete! {} file(s)").format(len(files)))
        self.status_text.SetForegroundColour(wx.Colour(0, 128, 0))
        
        for file_info in files:
            filename = file_info.get('filename', 'output')
            data = file_info.get('data')
            is_svg = file_info.get('is_svg', False)
            
            if data:
                if is_svg:
                    try:
                        svg_text = data.decode('utf-8')
                        self.preview_panel.add_svg(svg_text, filename)
                    except Exception as e:
                        import traceback
                        traceback.print_exc(file=sys.stderr)
                        self.preview_panel.add_image_data(data, filename)
                else:
                    self.preview_panel.add_image_data(data, filename)
        
        self.Layout()
    
    def _on_generation_error(self, error_message):
        """Handle generation error (called from main thread)."""
        self.generating = False
        self.generate_button.Enable(True)
        self.status_text.SetLabel(_("Error: {}").format(error_message))
        self.status_text.SetForegroundColour(wx.Colour(200, 0, 0))
        
        wx.MessageBox(
            _("Generation failed:\n\n{}").format(error_message),
            _("AI SVG Generator Error"),
            wx.OK | wx.ICON_ERROR
        )
