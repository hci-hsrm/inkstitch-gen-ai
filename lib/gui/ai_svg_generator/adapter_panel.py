import wx

from ...i18n import _
from ...comfyui_adapter import get_available_workflows


class AdapterPanel(wx.Panel):
    """Adapter tab panel for configuring the inference model and workflow."""

    def __init__(self, parent, on_workflow_changed=None):
        super().__init__(parent, wx.ID_ANY)
        
        self.on_workflow_changed = on_workflow_changed

        sizer = wx.BoxSizer(wx.VERTICAL)

        url_label = wx.StaticText(self, label=_("ComfyUI Server Address:"))
        sizer.Add(url_label, 0, wx.ALL, 5)

        self.url_input = wx.TextCtrl(self, size=(-1, -1))
        self.url_input.SetValue("http://localhost:8188")
        self.url_input.SetToolTip(_("Address of the ComfyUI server (e.g., http://localhost:8188)"))
        sizer.Add(self.url_input, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        sizer.Add((0, 15), 0, 0, 0)

        workflow_sizer = wx.BoxSizer(wx.HORIZONTAL)

        workflow_label = wx.StaticText(self, label=_("Workflow:"))
        workflow_sizer.Add(workflow_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        self.workflow_names = get_available_workflows()
        workflow_display_names = [self._format_workflow_name(name) for name in self.workflow_names]
        
        self.workflow_dropdown = wx.Choice(self, choices=workflow_display_names)
        if self.workflow_names:
            self.workflow_dropdown.SetSelection(0)
        self.workflow_dropdown.Bind(wx.EVT_CHOICE, self._on_workflow_selected)
        workflow_sizer.Add(self.workflow_dropdown, 1, wx.EXPAND)

        sizer.Add(workflow_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.workflow_desc = wx.StaticText(self, label="")
        self.workflow_desc.SetForegroundColour(wx.Colour(128, 128, 128))
        self.workflow_desc.Wrap(300)
        sizer.Add(self.workflow_desc, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        
        self._update_workflow_description()

        self.SetSizer(sizer)
    
    def _format_workflow_name(self, name):
        """Format workflow class name for display."""
        import re
        name = name.replace("WorkflowBuilder", "")
        words = re.sub('([A-Z])', r' \1', name).strip()
        return words
    
    def _on_workflow_selected(self, event):
        """Handle workflow selection change."""
        self._update_workflow_description()
        if self.on_workflow_changed:
            self.on_workflow_changed(self.get_workflow_name())
    
    def _update_workflow_description(self):
        """Update the workflow description text."""
        workflow_name = self.get_workflow_name()
        if workflow_name:
            from ...comfyui_adapter import get_workflow_builder
            builder_class = get_workflow_builder(workflow_name)
            if builder_class and builder_class.__doc__:
                desc = builder_class.__doc__.strip().split('\n')[0]
                self.workflow_desc.SetLabel(desc)
            else:
                self.workflow_desc.SetLabel("")
            self.workflow_desc.Wrap(300)

    def get_inference_url(self):
        """Return the ComfyUI server URL."""
        url = self.url_input.GetValue().strip()
        return url if url else "http://localhost:8188"

    def get_workflow_name(self):
        """Return the selected workflow name (class name from registry)."""
        selection = self.workflow_dropdown.GetSelection()
        if selection >= 0 and selection < len(self.workflow_names):
            return self.workflow_names[selection]
        return None
    
    def get_workflow_builder(self):
        """Return a new instance of the selected workflow builder."""
        from ...comfyui_adapter import get_workflow_builder
        workflow_name = self.get_workflow_name()
        if workflow_name:
            builder_class = get_workflow_builder(workflow_name)
            if builder_class:
                builder = builder_class()
                # Set the ComfyUI server URL on the workflow builder
                url = self.get_inference_url()
                if hasattr(builder, '_comfyui_url'):
                    builder._comfyui_url = url
                return builder
        return None
