import hashlib
import math
import os

def string_to_binary(s):
    """Convert a string to its binary representation."""
    return ''.join(format(byte, '08b') for byte in s.encode('utf-8'))

def calculate_original_entropy(s):
    """Calculate entropy of a given string."""
    if not s:
        return 0

    freq = {char: s.count(char) for char in set(s)}
    total_chars = len(s)

    entropy = -sum((count / total_chars) * math.log2(count / total_chars) for count in freq.values())
    return round(entropy, 4)

def generate_lfsr_values():
    """Generate two 64-bit values using a linear-feedback shift register (LFSR)."""
    value_1 = [1, 0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    value_2 = [1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

    # Apply LFSR to generate new 64-bit values
    lfsr_value_1 = value_1[:64]
    lfsr_value_2 = value_2[:64]

    return lfsr_value_1, lfsr_value_2

def generate_primary_key(value_1, value_2):
    """Generate the primary key using XOR and LFSR operations."""
    # XOR between value_1 and value_2
    primary_key = [v1 ^ v2 for v1, v2 in zip(value_1, value_2)]

    # Apply LFSR 64 roles on the primary key
    lfsr_primary_key = primary_key[:64]  # Simulate LFSR operation (truncate to 64 bits)

    return lfsr_primary_key

def block_processing_original(file_size):
    """Process the file size to calculate block information for the Original Algorithm."""
    block_size = 512  # Fixed block size
    file_size_bits = file_size * 8  # Convert file size to bits

    full_blocks = file_size_bits // block_size
    remaining_bits = file_size_bits % block_size
    bits_appended = 0

    if remaining_bits > 0:
        # If there are remaining bits, you need one extra full block
        full_blocks += 1
        bits_appended = block_size - remaining_bits
        memory_waste = bits_appended

    block_info = f"({full_blocks}) {block_size}-bit blocks"

    return block_info, bits_appended

def generate_original_hash(file_path):
    """Generate the original hash for the file."""
    # Step 1: Convert filename to binary
    filename = os.path.basename(file_path)
    filename_bin = string_to_binary(filename)

    # Step 2: Calculate file size in bits
    file_size_bits = len(filename_bin)

    # Step 3-7: Generate keys using LFSR and XOR
    value_1, value_2 = generate_lfsr_values()
    primary_key = generate_primary_key(value_1, value_2)

    # Step 8: Divide the message file into 512-bit blocks
    block_size = 512
    blocks = []
    data = filename_bin
    while len(data) >= block_size:
        blocks.append(data[:block_size])
        data = data[block_size:]
    if data:
        blocks.append(data.ljust(block_size, '0'))  # Pad the last block with zeros

    # Step 9: Apply MD5 hashing and retrieve the final hash
    md5_hash = hashlib.md5()
    for block in blocks:
        md5_hash.update(block.encode())

    final_hash = md5_hash.hexdigest()

    # Calculate block info and bits appended
    full_blocks = file_size_bits // block_size
    remaining_bits = file_size_bits % block_size
    bits_appended = 0 if remaining_bits == 0 else (block_size - remaining_bits)

    block_info = f"({full_blocks}) {block_size}-bit blocks"
    if remaining_bits > 0:
        block_info += f" and (1) {remaining_bits}-bit block"

    return final_hash, block_info, bits_appended