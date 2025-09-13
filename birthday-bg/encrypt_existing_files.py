"""
Script to encrypt existing files and convert them to hash-based filenames
"""

import os
import shutil
from crypto_utils import (save_encrypted_text_file, save_encrypted_binary_file, 
                         get_encrypted_path, get_file_hash)

def encrypt_existing_files():
    """Encrypt all existing resource files"""
    
    # Files to encrypt
    files_to_encrypt = [
        ('data.csv', 'text'),
        ('config.yaml', 'text'),
        ('bgs/template.png', 'binary'),
        ('bgs/default.png', 'binary')
    ]
    
    print("Starting file encryption process...")
    
    for original_path, file_type in files_to_encrypt:
        if os.path.exists(original_path):
            print(f"Encrypting {original_path}...")
            
            try:
                if file_type == 'text':
                    # Read text file
                    with open(original_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Encrypt and save
                    success = save_encrypted_text_file(original_path, content)
                    
                elif file_type == 'binary':
                    # Read binary file
                    with open(original_path, 'rb') as f:
                        content = f.read()
                    
                    # Encrypt and save
                    success = save_encrypted_binary_file(original_path, content)
                
                if success:
                    encrypted_path = get_encrypted_path(original_path)
                    file_hash = get_file_hash(original_path)
                    print(f"  ✓ Encrypted to: {encrypted_path}")
                    print(f"  ✓ Hash: {file_hash}")
                    
                    # Optionally backup original file
                    backup_path = f"{original_path}.backup"
                    shutil.copy2(original_path, backup_path)
                    print(f"  ✓ Backup created: {backup_path}")
                    
                else:
                    print(f"  ✗ Failed to encrypt {original_path}")
                    
            except Exception as e:
                print(f"  ✗ Error encrypting {original_path}: {e}")
        else:
            print(f"  ⚠ File not found: {original_path}")
    
    print("\nEncryption process completed!")
    print("\nEncrypted file mapping:")
    for original_path, _ in files_to_encrypt:
        encrypted_path = get_encrypted_path(original_path)
        file_hash = get_file_hash(original_path)
        print(f"  {original_path} -> {encrypted_path} (hash: {file_hash})")

if __name__ == "__main__":
    encrypt_existing_files()