"""Binary frame generator with metadata support."""

import struct
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union

from ..superbit.tokens import SuperBitGroup, SuperBitStream


@dataclass
class BinaryMetadata:
    """Metadata for binary frames."""
    compression_algorithm: Optional[str] = None
    compression_level: Optional[str] = None
    encryption_algorithm: Optional[str] = None
    encryption_key_id: Optional[str] = None
    encryption_nonce: Optional[str] = None
    encryption_tag: Optional[str] = None
    
    def to_bytes(self) -> bytes:
        """Convert metadata to bytes."""
        meta_dict = {
            'compression_algorithm': self.compression_algorithm,
            'compression_level': self.compression_level,
            'encryption_algorithm': self.encryption_algorithm,
            'encryption_key_id': self.encryption_key_id,
        }
        return json.dumps(meta_dict).encode('utf-8')


@dataclass
class BinaryFrame:
    """A binary frame containing compiled code with optional metadata."""
    header: bytes
    code: bytes
    constants: bytes
    metadata: Optional[BinaryMetadata] = None
    
    def to_bytes(self) -> bytes:
        """Convert frame to bytes."""
        result = self.header + self.code + self.constants
        if self.metadata:
            result += self.metadata.to_bytes()
        return result
    
    def __len__(self) -> int:
        """Get the size of the binary frame."""
        size = len(self.header) + len(self.code) + len(self.constants)
        if self.metadata:
            size += 2 + len(self.metadata.to_bytes()) - 2
        return size


class BinaryGenerator:
    """Generates binary frames from super-bit streams."""
    
    MAGIC_NUMBER = b'NULL'
    VERSION = 2
    
    def __init__(self):
        """Initialize binary generator."""
        self.metadata = BinaryMetadata()
    
    def set_compression_metadata(self, algorithm: Optional[str],
                                level: Optional[str]) -> None:
        """Set compression metadata.
        
        Args:
            algorithm: Compression algorithm name
            level: Compression level (low, medium, high)
        """
        self.metadata.compression_algorithm = algorithm
        self.metadata.compression_level = level
    
    def set_encryption_metadata(self, algorithm: Optional[str],
                               key_id: Optional[str],
                               nonce: Optional[str],
                               tag: Optional[str]) -> None:
        """Set encryption metadata.
        
        Args:
            algorithm: Encryption algorithm name
            key_id: Encryption key ID
            nonce: Nonce (hex string)
            tag: Authentication tag (hex string)
        """
        self.metadata.encryption_algorithm = algorithm
        self.metadata.encryption_key_id = key_id
        self.metadata.encryption_nonce = nonce
        self.metadata.encryption_tag = tag
    
    def generate(self, superbit_stream: Union[SuperBitGroup, SuperBitStream]) -> List[BinaryFrame]:
        """Generate binary frames from a super-bit stream."""
        header = self._generate_header()
        code = superbit_stream.to_bytes()
        constants = self._generate_constants_section()
        
        frame = BinaryFrame(
            header=header,
            code=code,
            constants=constants,
            metadata=self.metadata if any([
                self.metadata.compression_algorithm,
                self.metadata.encryption_algorithm
            ]) else None
        )
        return [frame]
    
    def _generate_header(self) -> bytes:
        """Generate the binary header."""
        header = self.MAGIC_NUMBER
        header += self.VERSION.to_bytes(1, 'big')
        header += b'\x00' * 11
        return header
    
    def _generate_constants_section(self) -> bytes:
        """Generate the constants section."""
        return b''
