"""Encryption/Decryption utilities for sensitive data"""
from cryptography.fernet import Fernet
import os
from typing import Optional
from config.config import settings


class EncryptionManager:
    """Manage encryption and decryption of sensitive data"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption manager
        
        Args:
            encryption_key: Base64 encoded encryption key. If not provided, 
                          will load from ENCRYPTION_KEY environment variable.
                          Generate new key: 
                          python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
        """
        if encryption_key is None:
            encryption_key = os.getenv("ENCRYPTION_KEY") or settings.encryption_key

        if not encryption_key:
            raise ValueError(
                "ENCRYPTION_KEY must be provided or set as environment variable. "
                "Generate new key: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        
        self.cipher = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data
        
        Args:
            data: String to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not data:
            return ""
        encrypted = self.cipher.encrypt(data.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
            
        Returns:
            Original decrypted string
        """
        if not encrypted_data:
            return ""
        try:
            decrypted = self.cipher.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create global encryption manager instance"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt_data(data: str) -> str:
    """Convenience function to encrypt data"""
    return get_encryption_manager().encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """Convenience function to decrypt data"""
    return get_encryption_manager().decrypt(encrypted_data)
