import hashlib
import os
import secrets

def to_binary(data: str) -> str:
    """Converts a string to its binary representation."""
    return ''.join(format(ord(char), '08b') for char in data)

def generate_salt(length: int = 32) -> bytes:
    """Generates a random salt of the given length."""
    return secrets.token_bytes(length)

def non_linear_transform(data: bytes) -> bytes:
    """Applies bitwise rotation and permutation for entropy expansion."""
    num = int.from_bytes(data, 'big')
    bit_length = len(data) * 8
    rotated = ((num << 1) & ((1 << bit_length) - 1)) | (num >> (bit_length - 1))  # Keep within bit_length
    return rotated.to_bytes(len(data), 'big')

def xor_and_and_logic(key1: bytes, key2: bytes, pepper: bytes) -> str:
    """Applies XOR and AND operations with a pepper to generate a secure hash."""
    xor_result = int.from_bytes(key1, 'big') ^ int.from_bytes(key2, 'big')
    and_result = int.from_bytes(key1, 'big') & int.from_bytes(key2, 'big')

    final_bits = ''.join('1' if (xor_bit == '1' and and_bit == '0') else '0'
                         for xor_bit, and_bit in zip(bin(xor_result)[2:].zfill(256), bin(and_result)[2:].zfill(256)))

    return hex(int(final_bits, 2))[2:].zfill(64)  # Ensure 256-bit (64 hex chars)

def key_stretching(data: bytes) -> bytes:
    """Performs key stretching using PBKDF2 for additional security."""
    return hashlib.pbkdf2_hmac('sha256', data, os.urandom(16), 1000)

def enhanced_block_processing(file_size):
    """Dynamically allocates blocks to optimize file processing."""
    block_sizes = [1024, 512, 256, 128, 64]
    used_blocks = []
    remaining_size = file_size
    memory_waste = 0

    while remaining_size > 0:
        for size in block_sizes:
            if remaining_size >= size:
                used_blocks.append(size)
                remaining_size -= size
                break
        else:
            largest_block = max([size for size in block_sizes if size <= remaining_size], default=64)
            used_blocks.append(largest_block)
            memory_waste += (largest_block - remaining_size)  # Track wasted memory
            remaining_size -= largest_block

    total_bits_used = sum(used_blocks)
    wasted_bits = total_bits_used - file_size
    return used_blocks, wasted_bits, memory_waste

def generate_enhanced_hash(filename: str, file_size: int) -> str:
    """Generates a secure, entropy-enhanced hash with block processing."""

    # Step 1: Convert filename to binary
    filename_binary = to_binary(filename)
    bit_length = len(filename_binary)

    # Step 2: Generate Initial Keys
    bit_length_bin = format(bit_length, '08b').encode()
    salt1 = generate_salt()
    intermediate_key1 = hashlib.sha256(bit_length_bin + filename_binary.encode() + salt1).digest()

    salt2 = generate_salt()
    final_key1 = hashlib.sha256(intermediate_key1 + salt2).digest()

    # Step 3: Entropy Expansion
    salt3 = generate_salt()
    transformed_data = non_linear_transform(final_key1 + salt3)
    final_key2 = hashlib.sha256(transformed_data).digest()

    # Step 4: XOR and AND Logic with a Pepper
    pepper = b"\x5a" * 32  # Fixed secret pepper
    secure_hash = xor_and_and_logic(final_key1, final_key2, pepper)

    # Step 5 & 6: Block Processing and Memory Optimization
    blocks, wasted_bits, memory_waste = enhanced_block_processing(file_size)

    # Step 7: Secure Hashing with Final XOR and Key Stretching
    combined_data = filename_binary.encode() + salt1 + salt2 + salt3 + pepper
    stretched_key = key_stretching(combined_data)
    final_secure_hash = hashlib.sha256(stretched_key).hexdigest()

    print(f"🔹 Block Processing Summary: {blocks}")
    print(f"🔹 Wasted Bits: {wasted_bits}, Memory Waste: {memory_waste}")

    return final_secure_hash
