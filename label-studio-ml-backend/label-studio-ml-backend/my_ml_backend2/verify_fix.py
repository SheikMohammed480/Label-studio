
import numpy as np
from rle_utils import create_rle_mask

def verify():
    # 1. Test binary mask (bool)
    mask = np.zeros((10, 10), dtype=bool)
    mask[2:5, 2:5] = True
    
    rle = create_rle_mask(mask)
    print(f"Mask type: {mask.dtype}, shape: {mask.shape}")
    print(f"RLE list type: {type(rle)}")
    print(f"RLE header (first 4 bytes - total length): {rle[:4]}")
    
    # Total pixels = 100, Channels = 4, Total values = 400
    # The header starts with a 32-bit big-endian(?) number.
    # encode_rle uses f'{num:032b}' which is big-endian bit string.
    # Bits 0-7, 8-15, 16-23, 24-31
    # 400 in binary is 0...000110010000
    # bits 24-31 (last byte): 10010000 = 144
    # bits 16-23 (third byte): 00000001 = 1
    # So header should be [0, 0, 1, 144]
    
    expected_header = [0, 0, 1, 144]
    if rle[:4] == expected_header:
        print("✅ Header length check passed (400 values for 10x10x4)")
    else:
        print(f"❌ Header length check failed. Expected {expected_header}, got {rle[:4]}")

    # 2. Test uint8 mask (0/1)
    mask_u8 = np.zeros((20, 20), dtype=np.uint8)
    mask_u8[5, 5] = 1
    rle_u8 = create_rle_mask(mask_u8)
    # Total values = 20*20*4 = 1600
    # 1600 = 00000000 00000000 00000110 01000000
    # Byte 3 = 6, Byte 4 = 64
    expected_header_u8 = [0, 0, 6, 64]
    if rle_u8[:4] == expected_header_u8:
        print("✅ Header length check passed (1600 values for 20x20x4)")
    else:
        print(f"❌ Header length check failed. Expected {expected_header_u8}, got {rle_u8[:4]}")

if __name__ == "__main__":
    try:
        verify()
    except Exception as e:
        print(f"Verification crashed: {e}")
