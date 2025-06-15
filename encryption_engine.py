# encryption_engine.py
"""
Custom Encryption Engine for CV Analyzer
Implementasi enkripsi hybrid dengan multiple layers tanpa pustaka bawaan
"""

import random
import time
import os

class AdvancedEncryption:
    def __init__(self, master_key="BukitDuri2024"):
        self.master_key = master_key
        self.key_matrix = self._generate_key_matrix()
        
    def _generate_key_matrix(self):
        """Generate dynamic key matrix dari master key"""
        seed = sum(ord(c) for c in self.master_key)
        random.seed(seed)
        return [[random.randint(1, 255) for _ in range(16)] for _ in range(16)]
    
    def _xor_cipher(self, data, key):
        """XOR cipher dengan rotating key"""
        result = bytearray()
        key_len = len(key)
        for i, byte in enumerate(data):
            result.append(byte ^ ord(key[i % key_len]))
        return bytes(result)
    
    def _substitution_cipher(self, data, encrypt=True):
        """Custom substitution cipher menggunakan key matrix"""
        result = bytearray()
        for byte in data:
            row = byte // 16
            col = byte % 16
            if encrypt:
                new_val = (self.key_matrix[row][col] + byte) % 256
            else:
                new_val = (byte - self.key_matrix[row][col]) % 256
            result.append(new_val)
        return bytes(result)
    
    def _permutation_cipher(self, data, encrypt=True):
        """Permutation cipher dengan block size 8"""
        block_size = 8
        result = bytearray()
        
        # Pola permutasi
        if encrypt:
            pattern = [3, 7, 1, 5, 0, 4, 2, 6]
        else:
            pattern = [4, 2, 6, 0, 5, 3, 7, 1]  # Reverse pattern
        
        for i in range(0, len(data), block_size):
            block = data[i:i + block_size]
            
            # Pad jika perlu
            while len(block) < block_size:
                block += b'\x00'
            
            # Apply permutation
            new_block = bytearray(block_size)
            for j in range(block_size):
                new_block[j] = block[pattern[j]]
            
            result.extend(new_block)
        
        return bytes(result)
    
    def _add_entropy(self, data):
        """Tambah entropy dengan timestamp dan random bytes"""
        timestamp = int(time.time()).to_bytes(4, 'big')
        random_bytes = bytes([random.randint(0, 255) for _ in range(4)])
        return timestamp + random_bytes + data
    
    def _remove_entropy(self, data):
        """Hapus entropy layer"""
        return data[8:]  # Skip 8 bytes (4 timestamp + 4 random)
    
    def encrypt(self, plaintext):
        """Multi-layer encryption"""
        if isinstance(plaintext, str):
            data = plaintext.encode('utf-8')
        else:
            data = plaintext
        
        # Layer 1: Add entropy
        data = self._add_entropy(data)
        
        # Layer 2: XOR dengan master key
        data = self._xor_cipher(data, self.master_key)
        
        # Layer 3: Substitution cipher
        data = self._substitution_cipher(data, encrypt=True)
        
        # Layer 4: Permutation cipher
        data = self._permutation_cipher(data, encrypt=True)
        
        # Layer 5: Final XOR dengan reversed key
        reversed_key = self.master_key[::-1]
        data = self._xor_cipher(data, reversed_key)
        
        # Convert ke hex untuk storage
        return data.hex()
    
    def decrypt(self, ciphertext):
        """Multi-layer decryption (reverse order)"""
        try:
            # Convert dari hex
            data = bytes.fromhex(ciphertext)
            
            # Layer 5: Reverse final XOR
            reversed_key = self.master_key[::-1]
            data = self._xor_cipher(data, reversed_key)
            
            # Layer 4: Reverse permutation
            data = self._permutation_cipher(data, encrypt=False)
            
            # Layer 3: Reverse substitution
            data = self._substitution_cipher(data, encrypt=False)
            
            # Layer 2: Reverse XOR
            data = self._xor_cipher(data, self.master_key)
            
            # Layer 1: Remove entropy
            data = self._remove_entropy(data)
            
            return data.decode('utf-8')
        except:
            return None

# Global encryption instance
encryption_engine = AdvancedEncryption()