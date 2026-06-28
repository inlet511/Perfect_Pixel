# Perfect Pixel

> **Auto detect and Get perfect Pixel art**

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

<img src="https://github.com/theamusing/perfectPixel/raw/main/assets/process.png" width="100%" />

Standard scaling often fails to sample AI-generated pixel art due to inconsistent sizes and non-square grids. 

This tool automatically detects the optimal grid and delivers perfectly aligned, pixel-perfect results.

## Features
- Automatically detect grid size from pixel style images.
- Refines AI generated pixel style image to perfectly aligned grids.
- Easy to integrate into your own workflow.

[Try the Web Demo](https://theamusing.github.io/perfectPixel_webdemo/)

## Installation

**Perfect Pixel** provides two implementations of the same core algorithm. The Lighweight Backend is designed in case you can't or don't want to use cv2. You can choose the one that best fits your environment:

| Feature | OpenCV Backend ([`perfect_pixel.py`](./src/perfect_pixel/perfect_pixel.py)) | Lightweight Backend ([`perfect_pixel_no_cv2.py`](./src/perfect_pixel/perfect_pixel_noCV2.py)) |
| :--- | :--- | :--- |
| **Dependencies** | `opencv-python`, `numpy` | `numpy` |

You can install Perfect Pixel via `pip`. It is recommended to install the OpenCV version for better performance.

```bash
# Recommended: Fast version with OpenCV support
pip install perfect-pixel[opencv]

# Numpy version: Lightweight (NumPy only)
pip install perfect-pixel
```

## Local Web UI

A local web page is available if you prefer uploading an image, setting the grid, previewing, and downloading the result in a browser — no ComfyUI required.

```bash
# install web deps (Flask + Pillow); numpy/opencv handled separately
uv pip install -e ".[web]"     # or: uv pip install flask pillow

# start the local server
uv run web/app.py
```

Then open <http://127.0.0.1:5000>. The page lets you:
- Upload an image.
- Choose **auto-detect** grid, or **manual** mode to set an exact grid count (e.g. 32×32).
- Click **预览网格 / Preview** to see the grid overlaid on the original.
- Click **处理 / Process** to generate the pixel-perfect result, then download the original-size PNG or an upscaled (nearest-neighbor) PNG.

The server only listens on `127.0.0.1`, so it is not exposed to your network.

## ComfyUI

A ComfyUI custom node is available for integrating Perfect Pixel into ComfyUI workflows.

- No changes to the core Perfect Pixel algorithm
- Provides a ComfyUI-friendly interface for pixel art refinement

- [`Learn how to use Perfect Pixel as a ComfyUI node`](integrations/comfyui/README.md)

## Usage 

### Step 1: Get pixel style image
First you need extra tools to get a pixel styled image. **The recommanded size is between 512 to 1024.**

You can use Stable Diffusion with any Pixel Style Lora, or you can use ChatGPT or Gemini to generate one.


For example, I used ChatGPT to transfer an image into pixel style.

```
prompt: Convert the input image into a TRUE perler bead pixel pattern designed for physical bead crafting, not digital illustration. Canvas size must be exactly 32×32 pixels OR 16×16 pixels, where each pixel represents exactly one perler bead. Use extremely large, chunky pixels with very few active pixels overall. Simplicity is critical. Only keep the main subject. Remove the entire background. For human characters, make sure the face is flat and no shadow. The subject must be centered with clear empty bead rows around all edges to allow easy mounting on a bead board. Add a clean, continuous dark outline around the subject so the silhouette is clearly readable when made with beads. Use a very limited solid color palette (maximum 6–8 colors total). No gradients, no shading, no lighting, no dithering, no texture. No anti-aliasing or smoothing — every pixel must be a perfect square bead aligned to the grid. The output image should be pixel-perfect, each grid only contains one color. Background must be pure solid white.
```

<img src="https://github.com/theamusing/perfectPixel/raw/main/assets/generated.png" width="50%" />

The image is in pixel style but the grids are distorted. Also we don't know the number of grids.

### Step 2: Use Perfect Pixel to refine your image

```python
import cv2
from perfect_pixel import get_perfect_pixel

bgr = cv2.imread("images/avatar.png", cv2.IMREAD_COLOR)
rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

w, h, out = get_perfect_pixel(rgb)
```

<img src="https://github.com/theamusing/perfectPixel/raw/main/assets/refined2.png" width="50%" />

*Also see [example.py](./example.py).*
```bash
python example.py
```

The grid size is automatically detected, and the image is refined.

<img src="https://github.com/theamusing/perfectPixel/raw/main/assets/process2.png" width="100%" />

Try integrate it into your own projects!

## API Reference

### `get_perfect_pixel(...)`

| Args | Description | 
| :--- | :--- |
| **image** | `RGB Image (H * W * 3)` |
| **sample_method** | `"center", "median" or "majority"` |
| **grid_size** | `Manually set the final grid as (grid_w, grid_h). When given, the image is divided into exactly that many cells (strict uniform division — no edge refinement, no fix_square), so the output is guaranteed to be grid_w × grid_h. Leave as None to auto-detect.` |
| **min_size** | `Minimum pixel size to consider valid` |
| **peak_width** | `Minimum peak width for peak detection.` |
| **refine_intensity** | `Intensity for grid line refinement. Recommended range is [0, 0.5]. Given original estimated grid line at x, the refinement will search in [x * (1 - refine_intensity), x * (1 + refine_intensity)].` |
| **fix_square** | `Whether to enforce output to be square when detected image is almost square. Ignored when grid_size is set.` |
| **debug** | `Whether to show debug plots.` |

| Returns | Description |
| :--- | :--- |
| **refined_w** | `Width of the refined image` |
| **refined_h** | `Height of the refined image` |
| **scaled_image** | `Refined Image(W * H * 3)` |

### `get_grid_preview(...)`

Returns the original image with the detected (or manually specified) grid drawn on top, as an RGB ndarray. Useful for inspecting the grid before sampling. Returns `None` if the grid could not be determined.

```python
from perfect_pixel import get_grid_preview

# auto-detected grid overlay
overlay = get_grid_preview(rgb)

# strict 32×32 grid overlay
overlay = get_grid_preview(rgb, grid_size=(32, 32))
```

| Args | Description |
| :--- | :--- |
| **image** | `RGB Image (H * W * 3)` |
| **grid_size** | `(grid_w, grid_h) for a strict uniform grid, or None to auto-detect` |
| **min_size / peak_width / refine_intensity** | `Same meaning as in get_perfect_pixel` |
| **color** | `Grid line color as an RGB tuple (default (255, 0, 0))` |
| **thickness** | `Grid line thickness in pixels (default 1)` |

### Manually setting the final grid

If you already know the exact pixel dimensions you want, pass `grid_size`:

```python
# force an exact 32×32 result, regardless of auto-detection
w, h, out = get_perfect_pixel(rgb, grid_size=(32, 32))
assert (w, h) == (32, 32)
```

## Algorithm

<img src="https://github.com/theamusing/perfectPixel/raw/main/assets/algorithm.png" width="100%" />

The whole algorithm mainly contains 3 steps:
1. Detect grid size from FFT magnitude of the original image and generate grids.
2. Detect edges using Sobel and refine the grids by aligning them to edges.
3. Use the grids to sample the original image and to get the scaled image.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=theamusing/perfectPixel&type=date&legend=top-left)](https://www.star-history.com/#theamusing/perfectPixel&type=date&legend=top-left)

Thanks so much!









