# Moving Target Defense Module for Dynamic CAN ID Mapping
# ────────────────────────────────────────────────────────────────────────
# AES-based masking for dynamic encryption of CAN IDs
# Exempts control ID (0x001) from encryption/decryption

import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Symmetric AES 16 byte key
AES_KEY = b'SecureECUSharedK'

dynamic_mode = True 

def _generate_mask():
    """
    Generate a pseudo-random mask using AES encryption of a time-based seed.
    
    Steps:
    - Take current minutes and seconds into a 16-byte block.
    - Encrypt using AES-ECB with the shared AES key.
    - Use the first two bytes, masked to 11 bits (0x7FF).
    """
    # Converts current time into seconds and turns that into 16 bytes (big endian)
    now = time.localtime()
    seed = (now.tm_min * 60 + now.tm_sec).to_bytes(16, byteorder='big') 

    cipher = AES.new(AES_KEY, AES.MODE_ECB)
    encrypted = cipher.encrypt(seed)
    
    # Takes the first 2 bytes from encrypted and turns them into an integer then masks to 11 bits
    mask = int.from_bytes(encrypted[:2], byteorder='big') & 0x7FF  # 11-bit mask
    return mask

def encrypt_id(base_id):
    """
    Encrypt a static CAN ID using the generated AES mask.
    Control messages (ID 0x001) are exempt and sent unencrypted.
    """
    if base_id == 0x001:
        return base_id  # Never encrypt control commands
    
    mask = _generate_mask()
    return base_id ^ mask  # XOR masking

def decrypt_id(received_id):
    """
    Decrypt a received CAN ID using the same AES mask.
    Control messages (ID 0x001) are exempt and processed directly.
    """
    if received_id == 0x001:
        return received_id  # Never decrypt control commands

    mask = _generate_mask()
    return received_id ^ mask  # XOR unmasking
