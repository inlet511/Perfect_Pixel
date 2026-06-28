
"""
Perfect Pixel: A library for auto grid detection and pixel art refinement.
"""

__version__ = "0.1.2"

from .perfect_pixel_noCV2 import get_perfect_pixel as _get_perfect_pixel_numpy
from .perfect_pixel_noCV2 import get_grid_preview as _get_grid_preview_numpy
from .perfect_pixel_noCV2 import compute_grid_coords as _compute_grid_coords_numpy

try:
    import cv2
    from .perfect_pixel import get_perfect_pixel as _get_perfect_pixel_opencv
    from .perfect_pixel import get_grid_preview as _get_grid_preview_opencv
    from .perfect_pixel import compute_grid_coords as _compute_grid_coords_opencv
    get_perfect_pixel = _get_perfect_pixel_opencv
    get_grid_preview = _get_grid_preview_opencv
    compute_grid_coords = _compute_grid_coords_opencv
except ImportError:
    _get_perfect_pixel_opencv = None
    _get_grid_preview_opencv = None
    _compute_grid_coords_opencv = None
    get_perfect_pixel = _get_perfect_pixel_numpy
    get_grid_preview = _get_grid_preview_numpy
    compute_grid_coords = _compute_grid_coords_numpy

__all__ = ["get_perfect_pixel", "get_grid_preview", "compute_grid_coords"]