import hashlib
import os
import math
from binascii import hexlify
from hashlib import pbkdf2_hmac

# Constants
LFSR_POLYNOMIAL = 0x80000057  # Example polynomial for LFSR (32-bit)
PBKDF2_ITERATIONS = 100000  # Key stretching iterations

# --- Helper Functions ---
def string_to_binary(s):
    return ''.join(format(byte, '08b') for byte in s.encode('utf-8'))

def lfsr(seed, polynomial, steps):
    """Linear Feedback Shift Register (LFSR) implementation."""
    state = seed
    for _ in range(steps):
        feedback = state & 1
        state >>= 1
        if feedback:
            state ^= polynomial
    return state

def generate_lfsr_key(value1, value2, steps=128):
    key1 = lfsr(value1, LFSR_POLYNOMIAL, steps)
    key2 = lfsr(value2, LFSR_POLYNOMIAL, steps)
    return (key1 << 32) | key2

def calculate_entropy(file_path):
    """Calculate the entropy of a file."""
    with open(file_path, "rb") as f:
        data = f.read()
    if not data:
        return 0

    # Count the frequency of each byte
    freq = {byte: data.count(byte) for byte in set(data)}
    total_bytes = len(data)

    # Calculate entropy
    entropy = -sum((count / total_bytes) * math.log2(count / total_bytes) for count in freq.values())
    return round(entropy, 4)

def generate_original_hash(file_path: str):
    """Generate the original hash for the file and calculate block details."""
    filename = os.path.basename(file_path)
    filename_bin = string_to_binary(filename)

    block_size = 512
    blocks = []
    data = filename_bin
    while len(data) >= block_size:
        blocks.append(data[:block_size])
        data = data[block_size:]
    if data:
        blocks.append(data.ljust(block_size, '0'))

    md5_hash = hashlib.md5()
    for block in blocks:
        for _ in range(5000):
            md5_hash.update(block.encode())

    final_hash = md5_hash.hexdigest()

    # Calculate block details
    file_size_bits = len(filename_bin)  # File size in bits
    full_blocks = file_size_bits // block_size
    remaining_bits = file_size_bits % block_size
    bits_appended = 0 if remaining_bits == 0 else (block_size - remaining_bits)

    block_info = f"({full_blocks}) {block_size}-bit blocks"
    if remaining_bits > 0:
        block_info += f" and (1) {remaining_bits}-bit block"

    return final_hash, block_info, bits_appended

