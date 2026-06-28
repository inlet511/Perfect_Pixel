"""Local web UI for Perfect Pixel.

Run with:  uv run web/app.py
Then open: http://127.0.0.1:5000
"""

import base64
import io
import os
import sys

import numpy as np
from flask import Flask, jsonify, render_template, request
from PIL import Image

# Make the repo root importable so `src.perfect_pixel` resolves the same way
# example.py does.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.perfect_pixel import (  # noqa: E402
    compute_grid_coords,
    get_grid_preview,
    get_perfect_pixel,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB upload cap


# ---- helpers ----

def _read_upload_as_rgb(file_storage):
    """Decode an uploaded image to a uint8 RGB ndarray. Raises ValueError on failure."""
    try:
        img = Image.open(file_storage.stream)
        img = img.convert("RGB")
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Cannot decode image: {exc}") from exc
    return np.asarray(img, dtype=np.uint8)


def _rgb_to_data_url(rgb):
    """Encode a uint8 RGB ndarray as a base64 PNG data URL."""
    if rgb.dtype != np.uint8:
        rgb = np.clip(np.rint(rgb), 0, 255).astype(np.uint8)
    img = Image.fromarray(rgb, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def remove_background(rgb, tolerance=30.0):
    """Make the solid color surrounding the subject transparent.

    Flood-fills from the image borders: any pixel reachable from an edge
    through colors within ``tolerance`` (Euclidean RGB distance) of the
    dominant border color becomes transparent. Solid-color regions enclosed
    by the subject are left untouched because they are not edge-connected.

    Args:
        rgb: uint8 RGB ndarray (H, W, 3).
        tolerance: color distance threshold; higher removes more.

    Returns:
        uint8 RGBA ndarray (H, W, 4).
    """
    rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
    H, W = rgb.shape[:2]
    rgba = np.dstack([rgb, np.full((H, W), 255, dtype=np.uint8)])
    if H == 0 or W == 0:
        return rgba

    flat = rgb.reshape(-1, 3).astype(np.int32)

    # Dominant color along the border is taken as the background reference.
    border = np.concatenate([
        rgb[0, :, :], rgb[-1, :, :], rgb[:, 0, :], rgb[:, -1, :]
    ], axis=0).astype(np.int32)
    colors, counts = np.unique(border, axis=0, return_counts=True)
    bg_color = colors[int(np.argmax(counts))]

    tol_sq = float(tolerance) * float(tolerance)
    diff = flat - bg_color[None, :]
    matches = np.einsum("ij,ij->i", diff, diff) <= tol_sq

    # BFS over the 4-connected grid, seeded from every border pixel that
    # matches the background color.
    visited = np.zeros(H * W, dtype=bool)
    stack = []
    for x in range(W):
        for idx in (x, (H - 1) * W + x):
            if matches[idx] and not visited[idx]:
                visited[idx] = True
                stack.append(idx)
    for y in range(H):
        for idx in (y * W, y * W + (W - 1)):
            if matches[idx] and not visited[idx]:
                visited[idx] = True
                stack.append(idx)

    while stack:
        idx = stack.pop()
        y, x = divmod(idx, W)
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < H and 0 <= nx < W:
                nidx = ny * W + nx
                if matches[nidx] and not visited[nidx]:
                    visited[nidx] = True
                    stack.append(nidx)

    alpha = rgba[..., 3].reshape(-1)
    alpha[visited] = 0
    return rgba


def _parse_grid(form):
    """Return (grid_size, refine_intensity) from the request form.

    grid_size is (w, h) in manual mode, else None.
    """
    mode = form.get("mode", "auto")
    refine_intensity = float(form.get("refine_intensity", 0.3))
    grid_size = None
    if mode == "manual":
        gw = int(float(form.get("grid_w", 32)))
        gh = int(float(form.get("grid_h", 32)))
        if gw < 1 or gh < 1:
            raise ValueError("Grid counts must be >= 1")
        grid_size = (gw, gh)
    return grid_size, refine_intensity


# ---- routes ----

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/preview", methods=["POST"])
def preview():
    if "image" not in request.files or request.files["image"].filename == "":
        return jsonify(error="No image uploaded"), 400
    try:
        rgb = _read_upload_as_rgb(request.files["image"])
        grid_size, refine_intensity = _parse_grid(request.form)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    x_coords, y_coords = compute_grid_coords(
        rgb, grid_size=grid_size, refine_intensity=refine_intensity
    )
    if x_coords is None:
        return jsonify(error="Failed to detect a grid. Try manual mode."), 400

    overlay = get_grid_preview(
        rgb, grid_size=grid_size, refine_intensity=refine_intensity,
        color=(255, 0, 0), thickness=1,
    )
    detected = [len(x_coords) - 1, len(y_coords) - 1]
    return jsonify(preview=_rgb_to_data_url(overlay), detected=detected)


@app.route("/process", methods=["POST"])
def process():
    if "image" not in request.files or request.files["image"].filename == "":
        return jsonify(error="No image uploaded"), 400
    try:
        rgb = _read_upload_as_rgb(request.files["image"])
        grid_size, refine_intensity = _parse_grid(request.form)
        sample_method = request.form.get("sample_method", "center")
        export_scale = max(1, int(float(request.form.get("export_scale", 8))))
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    w, h, out = get_perfect_pixel(
        rgb, sample_method=sample_method, grid_size=grid_size,
        refine_intensity=refine_intensity,
    )
    if w is None or h is None:
        return jsonify(error="Failed to detect a grid. Try manual mode."), 400

    if out.dtype != np.uint8:
        out = np.clip(np.rint(out), 0, 255).astype(np.uint8)

    remove_bg = request.form.get("remove_bg", "false").lower() in ("1", "true", "on", "yes")
    if remove_bg:
        try:
            bg_tolerance = float(request.form.get("bg_tolerance", 30))
        except (TypeError, ValueError):
            bg_tolerance = 30.0
        rgba = remove_background(out, tolerance=bg_tolerance)
        result_img = Image.fromarray(rgba, mode="RGBA")
        resample = Image.NEAREST
        scaled_img = result_img.resize((w * export_scale, h * export_scale), resample)
    else:
        result_img = Image.fromarray(out, mode="RGB")
        scaled_img = result_img.resize((w * export_scale, h * export_scale), Image.NEAREST)

    def _img_to_data_url(pil_img):
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"

    return jsonify(
        result=_img_to_data_url(result_img),
        result_scaled=_img_to_data_url(scaled_img),
        width=w,
        height=h,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
