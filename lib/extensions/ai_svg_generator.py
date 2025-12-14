# Authors: see git history
#
# Copyright (c) 2025 Authors
# Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.

import os
import sys
import traceback
import wx

from ..gui.ai_svg_generator import AISVGGeneratorPanel
from ..i18n import _
from ..utils import get_resource_dir
from .base import InkstitchExtension


class AISVGGeneratorFrame(wx.Frame):
    """Main frame for the AI SVG Generator."""

    def __init__(self, *args, **kwargs):
        super().__init__(None, wx.ID_ANY, _("AI SVG Generator"), *args, **kwargs)

        self.SetWindowStyle(wx.FRAME_FLOAT_ON_PARENT | wx.DEFAULT_FRAME_STYLE)

        # Set icon
        icon = wx.Icon(os.path.join(get_resource_dir("icons"), "inkstitch256x256.png"))
        self.SetIcon(icon)

        # Main panel
        self.panel = AISVGGeneratorPanel(self)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.SetSize(900, 600)
        self.Centre()

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        """Handle window close."""
        self.Destroy()


class AiSvgGenerator(InkstitchExtension):
    """Extension entry point for AI SVG Generator."""

    def effect(self) -> None:
        try:
            print("AI SVG Generator: Starting...", file=sys.stderr)
            print(f"Python path: {sys.path}", file=sys.stderr)
            
            app = wx.App()
            frame = AISVGGeneratorFrame()
            frame.Show()
            print("AI SVG Generator: Frame shown, entering main loop", file=sys.stderr)
            app.MainLoop()
            
        except Exception as e:
            print(f"AI SVG Generator Error: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            raise
