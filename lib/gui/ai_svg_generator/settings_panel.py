import wx
import wx.lib.scrolledpanel as scrolled

from ...i18n import _
from ...comfyui_adapter.builder_introspection import get_builder_methods_by_category


class SettingsPanel(scrolled.ScrolledPanel):
    """Settings tab panel with dynamic controls based on workflow builder."""

    def __init__(self, parent, workflow_name=None):
        super().__init__(parent, wx.ID_ANY)
        
        self.controls = {} 
        self.workflow_name = workflow_name
        
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.build_controls(workflow_name)
        
        self.SetSizer(self.main_sizer)
        self.SetupScrolling(scroll_x=False)
    
    def build_controls(self, workflow_name):
        """Build controls for the given workflow builder."""
        self.main_sizer.Clear(True)
        self.controls = {}
        
        if not workflow_name:
            placeholder = wx.StaticText(self, label=_("Select a workflow in the Adapter tab"))
            placeholder.SetForegroundColour(wx.Colour(128, 128, 128))
            self.main_sizer.Add(placeholder, 0, wx.ALL, 10)
            self.Layout()
            return
        
        from ...comfyui_adapter import get_workflow_builder
        builder_class = get_workflow_builder(workflow_name)
        
        if not builder_class:
            placeholder = wx.StaticText(self, label=_("Unknown workflow"))
            self.main_sizer.Add(placeholder, 0, wx.ALL, 10)
            self.Layout()
            return
        
        methods_by_category = get_builder_methods_by_category(builder_class)
        
        category_names = {
            "Prompt": _("Prompt Settings"),
            "Sampler": _("Sampler Settings"),
            "Image": _("Image Settings"),
            "Model": _("Model Settings"),
            "SVG": _("SVG Output Settings"),
            "API": _("API Settings"),
            "Other": _("Other Settings"),
        }
        
        category_order = ["Prompt", "Sampler", "Image", "Model", "SVG", "API", "Other"]
        
        for category in category_order:
            if category not in methods_by_category:
                continue
            
            methods = methods_by_category[category]
            
            header = wx.StaticText(self, label=category_names.get(category, category))
            header.SetFont(header.GetFont().Bold())
            self.main_sizer.Add(header, 0, wx.ALL, 5)
            
            line = wx.StaticLine(self)
            self.main_sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
            
            for method in methods:
                self._create_method_control(method)
            
            self.main_sizer.Add((0, 10), 0, 0, 0)
        
        self.Layout()
        self.SetupScrolling(scroll_x=False)
    
    def _create_method_control(self, method):
        """Create a control for a builder method."""
        if not method.params:
            return
        
        param = method.params[0]
        
        label_text = self._format_method_name(method.name) + ":"
        
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        label = wx.StaticText(self, label=label_text)
        label.SetMinSize((120, -1))
        hsizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        
        control = None
        
        if param.param_type in ('int', "<class 'int'>"):
            control = wx.SpinCtrl(self, min=0, max=10000)
            if param.default is not None:
                control.SetValue(int(param.default))
        elif param.param_type in ('float', "<class 'float'>"):
            control = wx.SpinCtrlDouble(self, min=0.0, max=100.0, inc=0.1)
            if param.default is not None:
                control.SetValue(float(param.default))
        elif param.param_type in ('bool', "<class 'bool'>"):
            control = wx.CheckBox(self)
            if param.default is not None:
                control.SetValue(bool(param.default))
        else:
            if method.name in ('prompt', 'subject', 'positive_prompt', 'character'):
                control = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(-1, 60))
            else:
                control = wx.TextCtrl(self, size=(200, -1))
            if param.default is not None:
                control.SetValue(str(param.default))
        
        tooltip_parts = []
        if method.description:
            tooltip_parts.append(method.description)
        if method.workflow_effect:
            tooltip_parts.append(f"Effect: {method.workflow_effect}")
        if param.description:
            tooltip_parts.append(f"Parameter: {param.description}")
        
        if tooltip_parts:
            control.SetToolTip('\n'.join(tooltip_parts))
        
        hsizer.Add(control, 1, wx.EXPAND)
        
        self.main_sizer.Add(hsizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        
        self.controls[method.name] = (control, param.name, param.param_type)
    
    def _format_method_name(self, name):
        """Format method name for display as label."""
        words = name.replace('_', ' ').title()
        return words
    
    def update_workflow(self, workflow_name):
        """Update controls for a new workflow."""
        self.workflow_name = workflow_name
        self.build_controls(workflow_name)
    
    def get_values(self):
        """Return a dict of method_name -> value for all controls."""
        values = {}
        for method_name, (control, param_name, param_type) in self.controls.items():
            if isinstance(control, wx.SpinCtrl):
                values[method_name] = control.GetValue()
            elif isinstance(control, wx.SpinCtrlDouble):
                values[method_name] = control.GetValue()
            elif isinstance(control, wx.CheckBox):
                values[method_name] = control.GetValue()
            elif isinstance(control, wx.TextCtrl):
                value = control.GetValue().strip()
                if value: 
                    values[method_name] = value
        return values
    
    def apply_to_builder(self, builder):
        """Apply all settings to a builder instance."""
        values = self.get_values()
        for method_name, value in values.items():
            if hasattr(builder, method_name):
                method = getattr(builder, method_name)
                try:
                    method(value)
                except Exception as e:
                    print(f"Error applying {method_name}({value}): {e}")
        return builder
