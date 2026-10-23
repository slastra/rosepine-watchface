import sys, math
from PIL import Image, ImageDraw, ImageFilter

W, H, K = 1080, 2400, 3          # draw at 3x, downsample for antialiasing
BASE, SURFACE, OVERLAY = (25, 23, 36), (31, 29, 46), (38, 35, 58)
ROSE, IRIS = (235, 188, 186), (196, 167, 231)

w, h = W * K, H * K
img = Image.new("RGB", (w, h), BASE)

# Gentle base -> surface gradient toward the bottom
grad = Image.linear_gradient("L").resize((w, h))
img = Image.composite(Image.new("RGB", (w, h), SURFACE), img, grad.point(lambda v: v * 0.8))

cx, cy, r = w // 2, int(h * 0.47), int(W * 0.40 * K)

# Iris glow behind the ring
glow = Image.new("L", (w, h), 0)
ImageDraw.Draw(glow).ellipse((cx - r, cy - r, cx + r, cy + r), fill=34)
glow = glow.filter(ImageFilter.GaussianBlur(r * 0.35))
img = Image.composite(Image.new("RGB", (w, h), IRIS), img, glow)

d = ImageDraw.Draw(img)
def ring(rad, width, color, start=-90, end=270, caps=False):
    box = (cx - rad, cy - rad, cx + rad, cy + rad)
    d.arc(box, start, end, fill=color, width=width)
    if caps:
        for a in (start, end):
            t = math.radians(a); m = rad - width / 2
            x, y = cx + m * math.cos(t), cy + m * math.sin(t)
            d.ellipse((x - width / 2, y - width / 2, x + width / 2, y + width / 2), fill=color)

stroke = 14 * K
ring(r, stroke, OVERLAY)                               # track
ring(r, stroke, ROSE, -90, 180, caps=True)             # 75% progress, like the watch
ring(r - 56 * K, 3 * K, tuple(int(c * 0.55 + b * 0.45) for c, b in zip(IRIS, BASE)))  # thin iris inner ring

img.resize((W, H), Image.LANCZOS).save(sys.argv[1])
