
import numpy as np

def bits2byte(arr_str, n=8):
    """Convert bits back to byte"""
    rle = []
    numbers = [arr_str[i : i + n] for i in range(0, len(arr_str), n)]
    for i in numbers:
        rle.append(int(i, 2))
    return rle

def base_rle_encode(inarray):
    """run length encoding. Partial credit to R rle function.
    Multi datatype arrays catered for including non Numpy
    returns: tuple (runlengths, startpositions, values)"""
    ia = np.asarray(inarray)  # force numpy
    n = len(ia)
    if n == 0:
        return None, None, None
    else:
        y = ia[1:] != ia[:-1]  # pairwise unequal (string safe)
        i = np.append(np.where(y), n - 1)  # must include last element posi
        z = np.diff(np.append(-1, i))  # run lengths
        p = np.cumsum(np.append(0, z))[:-1]  # positions
        return z, p, ia[i]

def encode_rle(arr, wordsize=8, rle_sizes=[3, 4, 8, 16]):
    """Encode a 1d array to rle"""
    # Set length of array in 32 bits
    num = len(arr)
    numbits = f'{num:032b}'

    # put in the wordsize in bits
    wordsizebits = f'{wordsize - 1:05b}'

    # put rle sizes in the bits
    rle_bits = ''.join([f'{x - 1:04b}' for x in rle_sizes])

    # combine it into base string
    base_str = numbits + wordsizebits + rle_bits

    # start with creating the rle bite string
    out_str = ''
    for length_reeks, p, value in zip(*base_rle_encode(arr)):
        if length_reeks == 1:
            out_str += '0'
            out_str += '00'
            out_str += '000'
            out_str += f'{value:08b}'
        elif length_reeks > 1:
            if length_reeks <= 8:
                out_str += '1'
                out_str += '00'
                out_str += f'{length_reeks - 1:03b}'
                out_str += f'{value:08b}'
            elif 8 < length_reeks <= 16:
                out_str += '1'
                out_str += '01'
                out_str += f'{length_reeks - 1:04b}'
                out_str += f'{value:08b}'
            elif 16 < length_reeks <= 256:
                out_str += '1'
                out_str += '10'
                out_str += f'{length_reeks - 1:08b}'
                out_str += f'{value:08b}'
            else:
                length_temp = length_reeks
                while length_temp > 2**16:
                    out_str += '1'
                    out_str += '11'
                    out_str += f'{2 ** 16 - 1:016b}'
                    out_str += f'{value:08b}'
                    length_temp -= 2**16
                out_str += '1'
                out_str += '11'
                out_str += f'{length_temp - 1:016b}'
                out_str += f'{value:08b}'

    nzfill = 8 - len(base_str + out_str) % 8
    if nzfill == 8: nzfill = 0
    total_str = base_str + out_str + nzfill * '0'
    rle = bits2byte(total_str)
    return rle

def create_rle_mask(mask: np.ndarray) -> list:
    """Convert binary/uint8 mask to official Label Studio RLE (RGBA bitstream)"""
    # ensure mask is uint8 and has values 0 and 255 for foreground
    if mask.dtype == bool:
        mask = mask.astype(np.uint8) * 255
    elif np.max(mask) == 1:
        mask = mask * 255
    
    # Flatten and repeat 4 times for RGBA (Label Studio requirement)
    array = mask.ravel()
    array = np.repeat(array, 4)
    
    # Encode using official bitstream logic
    return encode_rle(array)
