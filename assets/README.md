# Assets

Place your icon file here:
- `icon.ico` - Windows icon for the .exe (256x256 recommended)

## Creating an icon

You can create an icon from a PNG using online tools:
- https://convertio.co/png-ico/
- https://icoconvert.com/

Or use ImageMagick:
```bash
magick convert logo.png -define icon:auto-resize=256,128,64,48,32,16 icon.ico
```
