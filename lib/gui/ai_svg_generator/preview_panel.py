import io
import os
import subprocess
import tempfile
import wx
from wx.lib.scrolledpanel import ScrolledPanel

from ...i18n import _


class ImagePreviewItem(wx.Panel):
    """A single image preview with Save and Select buttons."""

    def __init__(self, parent, image_id, bitmap=None, svg_data=None, image_data=None, filename=None):
        super().__init__(parent, wx.ID_ANY)
        self.image_id = image_id
        self.parent_panel = parent
        self.svg_data = svg_data
        self.image_data = image_data  # Raw image bytes
        self.filename = filename or f"output_{image_id}.svg"
        self.image_path = None

        self.SetBackgroundColour(wx.Colour(240, 240, 240))

        sizer = wx.BoxSizer(wx.VERTICAL)

        if filename:
            name_label = wx.StaticText(self, label=filename)
            name_label.SetFont(name_label.GetFont().Bold())
            sizer.Add(name_label, 0, wx.ALL | wx.ALIGN_CENTER, 3)

        if bitmap:
            self.image_ctrl = wx.StaticBitmap(self, bitmap=bitmap)
        else:
            self.image_ctrl = wx.Panel(self, size=(200, 200))
            self.image_ctrl.SetBackgroundColour(wx.Colour(200, 200, 200))

            placeholder_sizer = wx.BoxSizer(wx.VERTICAL)
            placeholder_sizer.AddStretchSpacer()
            placeholder_text = wx.StaticText(self.image_ctrl, label=_("Generated SVG"))
            placeholder_text.SetForegroundColour(wx.Colour(100, 100, 100))
            placeholder_sizer.Add(placeholder_text, 0, wx.ALIGN_CENTER)
            placeholder_sizer.AddStretchSpacer()
            self.image_ctrl.SetSizer(placeholder_sizer)

        sizer.Add(self.image_ctrl, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.save_button = wx.Button(self, label=_("Save"))
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save)
        button_sizer.Add(self.save_button, 1, wx.RIGHT, 5)

        self.select_button = wx.Button(self, label=_("Select"))
        self.select_button.Bind(wx.EVT_BUTTON, self.on_select)
        button_sizer.Add(self.select_button, 1, wx.LEFT, 5)

        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)

    def on_save(self, event):
        if self.svg_data:
            # Save SVG data
            default_name = self.filename if self.filename.endswith('.svg') else f"{self.filename}.svg"
            with wx.FileDialog(
                self,
                _("Save SVG"),
                defaultFile=default_name,
                wildcard="SVG files (*.svg)|*.svg",
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            ) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    filepath = dlg.GetPath()
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(self.svg_data)
                    wx.MessageBox(
                        _("SVG saved to:\n{}").format(filepath),
                        _("Save Complete"),
                        wx.OK | wx.ICON_INFORMATION
                    )
        elif self.image_data:
            default_name = self.filename
            wildcard = "PNG files (*.png)|*.png|All files (*.*)|*.*"
            if self.filename.endswith('.jpg') or self.filename.endswith('.jpeg'):
                wildcard = "JPEG files (*.jpg)|*.jpg|All files (*.*)|*.*"
            
            with wx.FileDialog(
                self,
                _("Save Image"),
                defaultFile=default_name,
                wildcard=wildcard,
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            ) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    filepath = dlg.GetPath()
                    with open(filepath, 'wb') as f:
                        f.write(self.image_data)
                    wx.MessageBox(
                        _("Image saved to:\n{}").format(filepath),
                        _("Save Complete"),
                        wx.OK | wx.ICON_INFORMATION
                    )
        elif self.image_path:
            default_name = os.path.basename(self.image_path)
            wildcard = "All files (*.*)|*.*"
            if self.image_path.endswith('.svg'):
                wildcard = "SVG files (*.svg)|*.svg"
            elif self.image_path.endswith('.png'):
                wildcard = "PNG files (*.png)|*.png"
            
            with wx.FileDialog(
                self,
                _("Save File"),
                defaultFile=default_name,
                wildcard=wildcard,
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            ) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    import shutil
                    shutil.copy2(self.image_path, dlg.GetPath())
                    wx.MessageBox(
                        _("File saved to:\n{}").format(dlg.GetPath()),
                        _("Save Complete"),
                        wx.OK | wx.ICON_INFORMATION
                    )
        else:
            wx.MessageBox(
                _("No data to save."),
                _("Save"),
                wx.OK | wx.ICON_WARNING
            )

    def on_select(self, event):
        """Handle select button click - insert SVG into the document."""
        # TODO: Implement document insertion
        wx.MessageBox(
            _("Select functionality will insert the SVG into your Inkscape document.\n\nThis feature is not yet implemented."),
            _("Select"),
            wx.OK | wx.ICON_INFORMATION
        )


class PreviewPanel(ScrolledPanel):
    """Right panel showing generated images with Save/Select buttons."""

    def __init__(self, parent):
        super().__init__(parent, wx.ID_ANY)
        self.SetupScrolling(scroll_x=False)

        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(self, label=_("Generated Images"))
        title_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        self.sizer.Add(title, 0, wx.ALL, 10)

        self.placeholder_text = wx.StaticText(
            self,
            label=_("Generated SVGs will appear here.\nClick 'Generate SVGs' to create images.")
        )
        self.placeholder_text.SetForegroundColour(wx.Colour(128, 128, 128))
        self.sizer.Add(self.placeholder_text, 0, wx.ALL, 10)

        self.images_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.images_sizer, 1, wx.EXPAND)

        self.SetSizer(self.sizer)

        self.image_count = 0
        self.image_items = []

    def add_placeholder_image(self):
        if self.placeholder_text.IsShown():
            self.placeholder_text.Hide()

        self.image_count += 1
        item = ImagePreviewItem(self, self.image_count)
        self.image_items.append(item)
        self.images_sizer.Add(item, 0, wx.EXPAND | wx.ALL, 5)

        self.Layout()
        self.SetupScrolling(scroll_x=False)

    def add_image(self, bitmap, image_id=None, filename=None):
        """Add an image preview item with actual bitmap."""
        if self.placeholder_text.IsShown():
            self.placeholder_text.Hide()

        if image_id is None:
            self.image_count += 1
            image_id = self.image_count

        item = ImagePreviewItem(self, image_id, bitmap, filename=filename)
        self.image_items.append(item)
        self.images_sizer.Add(item, 0, wx.EXPAND | wx.ALL, 5)

        self.Layout()
        self.SetupScrolling(scroll_x=False)
    
    def add_svg(self, svg_data, filename=None):
        """Add an SVG to the preview panel."""
        if self.placeholder_text.IsShown():
            self.placeholder_text.Hide()
        
        self.image_count += 1
        
        bitmap = self._render_svg_to_bitmap(svg_data)
        
        item = ImagePreviewItem(self, self.image_count, bitmap, svg_data=svg_data, filename=filename)
        self.image_items.append(item)
        self.images_sizer.Add(item, 0, wx.EXPAND | wx.ALL, 5)

        self.Layout()
        self.SetupScrolling(scroll_x=False)
    
    def add_image_data(self, image_data, filename=None):
        """Add an image from raw bytes data."""
        if self.placeholder_text.IsShown():
            self.placeholder_text.Hide()
        
        self.image_count += 1
        
        # Convert bytes to bitmap
        bitmap = None
        try:
            stream = io.BytesIO(image_data)
            image = wx.Image(stream)
            if image.IsOk():
                # Scale to fit
                image = self._scale_image(image, 200)
                bitmap = wx.Bitmap(image)
        except Exception as e:
            print(f"Error loading image: {e}")
            bitmap = None
        
        # Store both the bitmap for display and the raw data for saving
        item = ImagePreviewItem(self, self.image_count, bitmap, image_data=image_data, filename=filename)
        self.image_items.append(item)
        self.images_sizer.Add(item, 0, wx.EXPAND | wx.ALL, 5)

        self.Layout()
        self.SetupScrolling(scroll_x=False)
    
    def _render_svg_to_bitmap(self, svg_data, size=200):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as svg_file:
            svg_file.write(svg_data)
            svg_path = svg_file.name
        
        png_path = svg_path.replace('.svg', '.png')
        
        try:
            subprocess.run([
                'inkscape',
                '--export-filename=' + png_path,
                '--export-width=' + str(size),
                '--export-height=' + str(size),
                svg_path
            ], capture_output=True, timeout=5, check=True)
            
            image = wx.Image(png_path)
            bitmap = wx.Bitmap(image) if image.IsOk() else None
            
            if os.path.exists(svg_path):
                os.unlink(svg_path)
            if os.path.exists(png_path):
                os.unlink(png_path)
            
            return bitmap if bitmap else self._create_placeholder_bitmap(size)
        except Exception as e:
            if os.path.exists(svg_path):
                os.unlink(svg_path)
            if os.path.exists(png_path):
                os.unlink(png_path)
            return self._create_placeholder_bitmap(size)
    
    def _create_placeholder_bitmap(self, size=200):
        bitmap = wx.Bitmap(size, size)
        dc = wx.MemoryDC(bitmap)
        dc.SetBackground(wx.Brush(wx.Colour(240, 240, 240)))
        dc.Clear()
        dc.SetTextForeground(wx.Colour(100, 100, 100))
        dc.DrawText("SVG", size // 2 - 15, size // 2 - 8)
        dc.SelectObject(wx.NullBitmap)
        return bitmap
    
    def _scale_image(self, image, max_size):
        w, h = image.GetSize()
        if w > max_size or h > max_size:
            if w > h:
                new_w = max_size
                new_h = int(h * max_size / w)
            else:
                new_h = max_size
                new_w = int(w * max_size / h)
            image = image.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
        return image

    def clear_images(self):
        """Remove all image previews."""
        for item in self.image_items:
            item.Destroy()
        self.image_items = []
        self.image_count = 0
        self.placeholder_text.Show()
        self.Layout()
