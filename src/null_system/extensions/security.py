"""Security layer for Null-Lang with encryption and key management.

Provides SuperBitSecurityLayer for AES-GCM encryption of binary frames,
and KeyManager for managing encryption keys and metadata.
"""

import os
import json
import hashlib
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Union
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from ..superbit.tokens import SuperBitStream, SuperBitToken


@dataclass
class EncryptionConfig:
    """Configuration for encryption operations."""
    algorithm: str = "AES-256-GCM"
    key_derivation: str = "PBKDF2"
    iterations: int = 100000
    salt_length: int = 16
    nonce_length: int = 12
    tag_length: int = 16


@dataclass
class KeyMetadata:
    """Metadata for an encryption key."""
    key_id: str
    algorithm: str
    created_at: str
    rotation_date: Optional[str] = None
    is_active: bool = True
    comment: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyMetadata":
        """Create from dictionary."""
        return cls(**data)


class KeyManager:
    """Manages encryption keys with persistence and derivation.
    
    Features:
    - Load/derive keys from CLI flags or config files
    - Persist metadata (key id, rotation)
    - Support multiple keys with versioning
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize KeyManager.
        
        Args:
            config_dir: Directory to store key metadata. Defaults to ~/.null_security
        """
        self.config_dir = config_dir or Path.home() / ".null_security"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.keys: Dict[str, bytes] = {}
        self.metadata: Dict[str, KeyMetadata] = {}
        self._load_metadata()
    
    def _load_metadata(self) -> None:
        """Load key metadata from disk."""
        metadata_file = self.config_dir / "keys.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                data = json.load(f)
                for key_id, meta in data.items():
                    self.metadata[key_id] = KeyMetadata.from_dict(meta)
    
    def _save_metadata(self) -> None:
        """Save key metadata to disk."""
        metadata_file = self.config_dir / "keys.json"
        data = {key_id: meta.to_dict() for key_id, meta in self.metadata.items()}
        with open(metadata_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def derive_key(self, password: str, salt: Optional[bytes] = None,
                   iterations: int = 100000) -> tuple[bytes, bytes]:
        """Derive a key from a password using PBKDF2.
        
        Args:
            password: Password to derive from
            salt: Optional salt. Generated if not provided
            iterations: Number of iterations for PBKDF2
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())
        return key, salt
    
    def create_key(self, key_id: Optional[str] = None,
                   password: Optional[str] = None,
                   comment: Optional[str] = None) -> tuple[str, bytes]:
        """Create a new encryption key.
        
        Args:
            key_id: Optional key ID. Generated if not provided
            password: Optional password to derive key from. If not provided, generates random key
            comment: Optional comment for the key
            
        Returns:
            Tuple of (key_id, key_bytes)
        """
        if key_id is None:
            key_id = f"key-{uuid.uuid4().hex[:12]}"
        
        if password:
            key, salt = self.derive_key(password)
            salt_file = self.config_dir / f"{key_id}.salt"
            with open(salt_file, "wb") as f:
                f.write(salt)
        else:
            key = os.urandom(32)
        
        self.keys[key_id] = key
        self.metadata[key_id] = KeyMetadata(
            key_id=key_id,
            algorithm="AES-256-GCM",
            created_at=datetime.utcnow().isoformat(),
            is_active=True,
            comment=comment
        )
        
        key_file = self.config_dir / f"{key_id}.key"
        with open(key_file, "wb") as f:
            f.write(key)
        
        self._save_metadata()
        return key_id, key
    
    def load_key(self, key_id: str, password: Optional[str] = None) -> bytes:
        """Load a key by ID.
        
        Args:
            key_id: ID of the key to load
            password: Optional password if key was derived
            
        Returns:
            The key bytes
            
        Raises:
            ValueError: If key not found
        """
        if key_id in self.keys:
            return self.keys[key_id]
        
        key_file = self.config_dir / f"{key_id}.key"
        if not key_file.exists():
            raise ValueError(f"Key '{key_id}' not found")
        
        with open(key_file, "rb") as f:
            key = f.read()
        
        salt_file = self.config_dir / f"{key_id}.salt"
        if salt_file.exists() and password:
            with open(salt_file, "rb") as f:
                salt = f.read()
            key, _ = self.derive_key(password, salt)
        
        self.keys[key_id] = key
        return key
    
    def get_active_key(self) -> tuple[str, bytes]:
        """Get the currently active key.
        
        Returns:
            Tuple of (key_id, key_bytes)
            
        Raises:
            ValueError: If no active key exists
        """
        for key_id, meta in self.metadata.items():
            if meta.is_active:
                key = self.load_key(key_id)
                return key_id, key
        
        raise ValueError("No active encryption key found")
    
    def list_keys(self) -> List[KeyMetadata]:
        """List all available keys."""
        return list(self.metadata.values())
    
    def rotate_key(self, old_key_id: str, new_password: Optional[str] = None) -> tuple[str, bytes]:
        """Rotate a key by creating a new one and marking old as inactive.
        
        Args:
            old_key_id: ID of key to rotate
            new_password: Optional password for new key
            
        Returns:
            Tuple of (new_key_id, new_key_bytes)
        """
        if old_key_id not in self.metadata:
            raise ValueError(f"Key '{old_key_id}' not found")
        
        self.metadata[old_key_id].is_active = False
        self.metadata[old_key_id].rotation_date = datetime.utcnow().isoformat()
        
        new_key_id, new_key = self.create_key(password=new_password)
        self._save_metadata()
        return new_key_id, new_key


class SuperBitSecurityLayer:
    """Security layer for encrypting and decrypting super-bit streams.
    
    Features:
    - AES-256-GCM encryption of binary frames
    - Opcode bit remapping per user keys
    - Helper APIs for encrypted messaging and file storage
    """
    
    def __init__(self, key_manager: Optional[KeyManager] = None,
                 config: Optional[EncryptionConfig] = None):
        """Initialize security layer.
        
        Args:
            key_manager: KeyManager instance. Creates default if not provided
            config: EncryptionConfig with algorithm settings
        """
        self.key_manager = key_manager or KeyManager()
        self.config = config or EncryptionConfig()
        self.opcode_map: Dict[str, str] = {}
    
    def encrypt_stream(self, stream: SuperBitStream,
                      key_id: Optional[str] = None) -> tuple[bytes, str, bytes, bytes]:
        """Encrypt a super-bit stream using AES-GCM.
        
        Args:
            stream: SuperBitStream to encrypt
            key_id: Key ID to use. Uses active key if not provided
            
        Returns:
            Tuple of (ciphertext, key_id, nonce, tag) for storage
        """
        if key_id is None:
            key_id, _ = self.key_manager.get_active_key()
        
        key = self.key_manager.load_key(key_id)
        nonce = os.urandom(12)
        
        plaintext = stream.to_bytes()
        
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        
        tag = ciphertext[-16:]
        actual_ciphertext = ciphertext[:-16]
        
        return actual_ciphertext, key_id, nonce, tag
    
    def decrypt_stream(self, ciphertext: bytes, key_id: str,
                      nonce: bytes, tag: bytes) -> SuperBitStream:
        """Decrypt a super-bit stream using AES-GCM.
        
        Args:
            ciphertext: Encrypted data
            key_id: Key ID used for encryption
            nonce: Nonce used for encryption
            tag: Authentication tag
            
        Returns:
            Decrypted SuperBitStream
            
        Raises:
            ValueError: If decryption fails (wrong key or corrupted data)
        """
        key = self.key_manager.load_key(key_id)
        
        cipher = AESGCM(key)
        plaintext = cipher.decrypt(nonce, ciphertext + tag, None)
        
        return SuperBitStream.from_bytes(plaintext)
    
    def encrypt_message(self, message: str,
                       key_id: Optional[str] = None) -> tuple[bytes, str, bytes, bytes]:
        """Encrypt a text message for secure messaging.
        
        Args:
            message: Message to encrypt
            key_id: Key ID to use
            
        Returns:
            Tuple of (ciphertext, key_id, nonce, tag)
        """
        if key_id is None:
            key_id, _ = self.key_manager.get_active_key()
        
        key = self.key_manager.load_key(key_id)
        nonce = os.urandom(12)
        plaintext = message.encode("utf-8")
        
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        
        tag = ciphertext[-16:]
        actual_ciphertext = ciphertext[:-16]
        
        return actual_ciphertext, key_id, nonce, tag
    
    def decrypt_message(self, ciphertext: bytes, key_id: str,
                       nonce: bytes, tag: bytes) -> str:
        """Decrypt a text message.
        
        Args:
            ciphertext: Encrypted message
            key_id: Key ID used for encryption
            nonce: Nonce used for encryption
            tag: Authentication tag
            
        Returns:
            Decrypted message string
        """
        key = self.key_manager.load_key(key_id)
        
        cipher = AESGCM(key)
        plaintext = cipher.decrypt(nonce, ciphertext + tag, None)
        
        return plaintext.decode("utf-8")
    
    def encrypt_file(self, input_path: Path, output_path: Path,
                    key_id: Optional[str] = None) -> Dict[str, str]:
        """Encrypt a file and save with metadata.
        
        Args:
            input_path: Path to file to encrypt
            output_path: Path to save encrypted file
            key_id: Key ID to use
            
        Returns:
            Metadata dictionary with key_id, nonce, tag (as hex strings)
        """
        if key_id is None:
            key_id, _ = self.key_manager.get_active_key()
        
        plaintext = input_path.read_bytes()
        key = self.key_manager.load_key(key_id)
        nonce = os.urandom(12)
        
        cipher = AESGCM(key)
        ciphertext = cipher.encrypt(nonce, plaintext, None)
        
        tag = ciphertext[-16:]
        actual_ciphertext = ciphertext[:-16]
        
        output_path.write_bytes(actual_ciphertext)
        
        return {
            "key_id": key_id,
            "nonce": nonce.hex(),
            "tag": tag.hex(),
            "algorithm": self.config.algorithm
        }
    
    def decrypt_file(self, input_path: Path, output_path: Path,
                    metadata: Dict[str, str]) -> None:
        """Decrypt a file using metadata.
        
        Args:
            input_path: Path to encrypted file
            output_path: Path to save decrypted file
            metadata: Metadata dictionary with key_id, nonce, tag
        """
        ciphertext = input_path.read_bytes()
        key_id = metadata["key_id"]
        nonce = bytes.fromhex(metadata["nonce"])
        tag = bytes.fromhex(metadata["tag"])
        
        key = self.key_manager.load_key(key_id)
        cipher = AESGCM(key)
        plaintext = cipher.decrypt(nonce, ciphertext + tag, None)
        
        output_path.write_bytes(plaintext)
    
    def remap_opcodes(self, key_id: str) -> Dict[str, str]:
        """Generate opcode remapping for obfuscation based on key.
        
        Args:
            key_id: Key to derive mapping from
            
        Returns:
            Dictionary mapping original opcodes to remapped values
        """
        key = self.key_manager.load_key(key_id)
        mapping = {}
        
        opcodes = [
            "LOAD_CONST", "LOAD_VAR", "STORE_VAR",
            "BINARY_ADD", "BINARY_SUB", "BINARY_MUL", "BINARY_DIV",
            "COMPARE_GT", "COMPARE_LT", "COMPARE_EQ",
            "JUMP", "JUMP_IF_FALSE", "PRINT", "NOP"
        ]
        
        for opcode in opcodes:
            hash_obj = hashlib.sha256(key + opcode.encode())
            hash_bytes = hash_obj.digest()[:8]
            remapped = f"0x{int.from_bytes(hash_bytes, 'big'):016x}"
            mapping[opcode] = remapped
        
        self.opcode_map = mapping
        return mapping
    
    def get_opcode_map(self) -> Dict[str, str]:
        """Get current opcode mapping."""
        return self.opcode_map.copy()
