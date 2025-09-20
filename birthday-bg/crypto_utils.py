import hashlib
import os

# XOR key for encryption/decryption
XOR_KEY = 0x7E

# File mapping - original name to hash
FILE_MAPPING = {
    "data.csv": "b87775cb83cbf0511096cfb67074662a.dat",
    "config.yaml": None,
    "bgs/template.png": None,
    "bgs/default.png": None,
}


def get_file_hash(filename):
    """Generate hash for filename"""
    return hashlib.md5(filename.encode()).hexdigest()


def get_encrypted_filename(original_filename):
    """Get encrypted filename based on hash"""
    file_hash = get_file_hash(original_filename)
    return f"{file_hash}.dat"


def xor_encrypt_decrypt(data):
    """XOR encrypt/decrypt data (same operation for both)"""
    if isinstance(data, str):
        data = data.encode("utf-8")

    result = bytearray()
    for byte in data:
        result.append(byte ^ XOR_KEY)

    return bytes(result)


def encrypt_file(source_path, encrypted_path):
    """Encrypt a file and save to encrypted path"""
    try:
        with open(source_path, "rb") as f:
            data = f.read()

        encrypted_data = xor_encrypt_decrypt(data)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(encrypted_path), exist_ok=True)

        with open(encrypted_path, "wb") as f:
            f.write(encrypted_data)

        return True
    except Exception as e:
        print(f"Error encrypting file {source_path}: {e}")
        return False


def decrypt_file(encrypted_path, output_path=None):
    """Decrypt a file and return data or save to output path"""
    try:
        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()

        decrypted_data = xor_encrypt_decrypt(encrypted_data)

        if output_path:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(decrypted_data)
            return True
        else:
            return decrypted_data
    except Exception as e:
        print(f"Error decrypting file {encrypted_path}: {e}")
        return None


def get_encrypted_path(original_path):
    """Get the encrypted path for an original file path"""
    encrypted_filename = get_encrypted_filename(original_path)

    # Keep directory structure but change filename
    if "/" in original_path:
        dir_path = os.path.dirname(original_path)
        return os.path.join(dir_path, encrypted_filename)
    else:
        return encrypted_filename


def load_encrypted_text_file(original_path, basepath=""):
    """Load and decrypt a text file, return as string"""
    encrypted_path = get_encrypted_path(original_path)
    encrypted_path = os.path.join(basepath, encrypted_path)

    if not os.path.exists(encrypted_path):
        return None

    decrypted_data = decrypt_file(encrypted_path)
    if decrypted_data:
        return decrypted_data.decode("utf-8")
    return None


def save_encrypted_text_file(original_path, content):
    """Encrypt and save text content to file"""
    encrypted_path = get_encrypted_path(original_path)

    # Create directory if needed
    if os.path.dirname(encrypted_path):
        os.makedirs(os.path.dirname(encrypted_path), exist_ok=True)

    encrypted_data = xor_encrypt_decrypt(content)

    try:
        with open(encrypted_path, "wb") as f:
            f.write(encrypted_data)
        return True
    except Exception as e:
        print(f"Error saving encrypted file {encrypted_path}: {e}")
        return False


def load_encrypted_binary_file(original_path, basepath=""):
    """Load and decrypt a binary file, return as bytes"""
    encrypted_path = get_encrypted_path(original_path)
    encrypted_path = os.path.join(basepath, encrypted_path)

    if not os.path.exists(encrypted_path):
        return None

    return decrypt_file(encrypted_path)


def save_encrypted_binary_file(original_path, data):
    """Encrypt and save binary data to file"""
    encrypted_path = get_encrypted_path(original_path)

    # Create directory if needed
    os.makedirs(os.path.dirname(encrypted_path), exist_ok=True)

    encrypted_data = xor_encrypt_decrypt(data)

    try:
        with open(encrypted_path, "wb") as f:
            f.write(encrypted_data)
        return True
    except Exception as e:
        print(f"Error saving encrypted binary file {encrypted_path}: {e}")
        return False


# Initialize file mapping
# for original_file in FILE_MAPPING.keys():
#     FILE_MAPPING[original_file] = get_encrypted_filename(original_file)
