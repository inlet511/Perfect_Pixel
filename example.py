import cv2
import matplotlib.pyplot as plt
from src.perfect_pixel import get_perfect_pixel, get_grid_preview

path = "images/girl.jpg"
# path = "images/avatar.png"
# path = "images/robot.jpeg"
# path = "images/shanxi.jpg"
# path = "images/skull.png"
# path = "images/rika.png"
# path = "images/car.png"

bgr = cv2.imread(path, cv2.IMREAD_COLOR)

if bgr is None:
    raise FileNotFoundError(f"Cannot read image: {path}")
rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

# Manually set the final grid here, or leave it None to auto-detect.
grid_size = None  # e.g. (32, 32) to force an exact 32x32 result

# Preview: overlay the grid on the original image before sampling.
preview = get_grid_preview(rgb, grid_size=grid_size, refine_intensity=0.3)

w, h, out = get_perfect_pixel(rgb, sample_method="center", grid_size=grid_size, refine_intensity=0.3, debug=False)

if w is None or h is None:
    print("Failed to generate pixel-perfect image.")
    exit(1)

# display
plt.figure(figsize=(14, 4))
plt.subplot(1, 3, 1)
plt.title("Input")
plt.imshow(rgb)
plt.axis("off")

plt.subplot(1, 3, 2)
plt.title("Grid Preview")
plt.imshow(preview if preview is not None else rgb)
plt.axis("off")

plt.subplot(1, 3, 3)
plt.title(f"Pixel-perfect ({w}×{h})")
plt.imshow(out)
plt.axis("off")

plt.show()

# save output
out_bgr = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
cv2.imwrite("output.png", out_bgr)

# save 8x scaled output
out_8x = cv2.resize(out_bgr, (w * 8, h * 8), interpolation=cv2.INTER_NEAREST)
cv2.imwrite("output_8x.png", out_8x)