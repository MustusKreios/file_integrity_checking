import hashlib
import os
import math
import binascii
from Crypto.Protocol.KDF import PBKDF2  # For key stretching

def string_to_binary(s):
    """Convert a string to its binary representation."""
    return ''.join(format(byte, '08b') for byte in s.encode('utf-8'))

def generate_random_salt(length=16):
    """Generate a random salt of the specified length."""
    return os.urandom(length)

def binary_to_hex(binary_string):
    """Convert a binary string to a hexadecimal string."""
    return hex(int(binary_string, 2))[2:].zfill(64)

def generate_enhanced_hash(file_path):
    """Generate an enhanced hash for the file."""
    # Step 1: Convert Filename to Binary
    filename = os.path.basename(file_path)
    filename_bin = string_to_binary(filename)
    total_bits = len(filename_bin)

    # Step 2: Generate a 256-bit Key
    total_bits_bin = format(total_bits, '08b')  # Convert total bit count to 8-bit binary
    concatenated_data = total_bits_bin + filename_bin

    salt1 = generate_random_salt()
    intermediate_key1 = hashlib.sha256(concatenated_data.encode() + salt1).hexdigest()

    salt2 = generate_random_salt()
    final_key1 = hashlib.sha256(intermediate_key1.encode() + salt2).hexdigest()

    # Step 3: Introduce Salt-Based Entropy Expansion
    salt3 = generate_random_salt()
    salt3_bin = string_to_binary(binascii.hexlify(salt3).decode())
    concatenated_entropy = salt3_bin + string_to_binary(final_key1)

    # Apply a non-linear transformation (bitwise rotation)
    transformed_data = concatenated_entropy[::-1]  # Reverse the binary string as a simple transformation
    final_key2 = hashlib.sha256(transformed_data.encode()).hexdigest()

    # Step 4: Apply XOR and AND Logic with a Pepper
    pepper = "secret_pepper"  # Replace with a secure constant value
    pepper_bin = string_to_binary(pepper)

    final_key1_bin = string_to_binary(final_key1)
    final_key2_bin = string_to_binary(final_key2)

    xor_result = ''.join(str(int(a) ^ int(b)) for a, b in zip(final_key1_bin, final_key2_bin))
    and_result = ''.join(str(int(a) & int(b)) for a, b in zip(final_key1_bin, final_key2_bin))

    # Apply custom rule
    final_binary_key = ''.join(
        '1' if xor_bit == '1' and and_bit == '0' else '0'
        for xor_bit, and_bit in zip(xor_result, and_result)
    )
    final_hex_key = binary_to_hex(final_binary_key)

    # Step 5: Optimize Block Processing
    file_size = os.path.getsize(file_path)
    block_info, bits_appended, memory_waste = enhanced_block_processing(file_size)

    # Step 7: Secure Hashing with Final XOR and Key Stretching
    combined_data = filename_bin + string_to_binary(binascii.hexlify(salt1).decode()) + \
                    string_to_binary(binascii.hexlify(salt2).decode()) + \
                    string_to_binary(binascii.hexlify(salt3).decode()) + pepper_bin

    xor_combined = ''.join(str(int(a) ^ int(b)) for a, b in zip(combined_data, final_key1_bin))
    stretched_key = PBKDF2(xor_combined, salt1, dkLen=32, count=1000)  # Key stretching with PBKDF2
    final_hash = hashlib.sha256(stretched_key).hexdigest()

    return final_hash

def enhanced_block_processing(file_size):
    """Process the file size to calculate block information using combined block sizes."""
    block_sizes = [1024, 512, 256, 128, 64]  # Available block sizes
    file_size_bits = file_size * 8  # Convert file size to bits

    block_info = ""
    bits_appended = 0  # Initialize with default value
    memory_waste = 0  # Initialize with default value
    remaining_bits = file_size_bits

    for block_size in block_sizes:
        # Calculate how many full blocks of the current block size fit in the remaining bits
        full_blocks_for_this_size = remaining_bits // block_size
        remaining_bits -= full_blocks_for_this_size * block_size  # Subtract the filled bits

        if full_blocks_for_this_size > 0:
            block_info += f"({full_blocks_for_this_size}) {block_size}-bit blocks\n, "

    # Handle remaining bits with the smallest block size
    if remaining_bits > 0:
        last_block_size = block_sizes[-1]  # The smallest block size
        block_info += f"and (1) {last_block_size}-bit block\n"
        bits_appended = last_block_size - remaining_bits  # Padding needed to fill the last block
        memory_waste = bits_appended  # Memory waste due to padding

    # Remove trailing comma and space from block_info
    block_info = block_info.rstrip(", ")

    return block_info, bits_appended, memory_waste

def calculate_entropy(s):
    """Calculate entropy of a given string."""
    if not s:
        return 0

    freq = {char: s.count(char) for char in set(s)}
    total_chars = len(s)

    entropy = -sum((count / total_chars) * math.log2(count / total_chars) for count in freq.values())
    return round(entropy, 4)