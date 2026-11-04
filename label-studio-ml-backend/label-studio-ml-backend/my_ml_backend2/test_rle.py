
import numpy as np
from label_studio_converter.brush import mask2rle

def custom_create_rle_mask(mask: np.ndarray) -> list:
    mask_flat = mask.flatten(order="C").astype(np.uint8)
    n = len(mask_flat)
    rle: list = []
    i = 0
    while i < n:
        val = int(mask_flat[i])
        count = 1
        while i + count < n and mask_flat[i + count] == val and count < 255:
            count += 1
        rle.append(count)
        rle.append(val)
        i += count
    return rle

# Create a simple 10x10 mask
mask = np.zeros((10, 10), dtype=np.uint8)
mask[2:5, 2:5] = 1

print("Official mask2rle output:")
try:
    official_rle = mask2rle(mask)
    print(official_rle[:20], "...")
    print("Type:", type(official_rle))
    if isinstance(official_rle, list):
        print("Length:", len(official_rle))
except Exception as e:
    print("Error calling official mask2rle:", e)

print("\nCustom create_rle_mask output:")
custom_rle = custom_create_rle_mask(mask)
print(custom_rle[:20], "...")
print("Length:", len(custom_rle))
