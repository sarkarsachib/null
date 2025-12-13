"""Binary frame generator with metadata support."""

import struct
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from ..superbit.tokens import SuperBitGroup


@dataclass
class BinaryMetadata:
    """Metadata for binary frames."""
    compression_algorithm: Optional[str] = None
    compression_level: Optional[str] = None
    encryption_algorithm: Optional[str] = None
    encryption_key_id: Optional[str] = None
    encryption_nonce: Optional[str] = None
    encryption_tag: Optional[str] = None
    custom: Dict[str, Any] = field(default_factory=dict)
    
    def to_bytes(self) -> bytes:
        """Serialize metadata to bytes."""
        data = {
            "compression_algorithm": self.compression_algorithm,
            "compression_level": self.compression_level,
            "encryption_algorithm": self.encryption_algorithm,
            "encryption_key_id": self.encryption_key_id,
            "encryption_nonce": self.encryption_nonce,
            "encryption_tag": self.encryption_tag,
            "custom": self.custom
        }
        json_bytes = json.dumps(data).encode("utf-8")
        return struct.pack(">H", len(json_bytes)) + json_bytes
    
    @staticmethod
    def from_bytes(data: bytes) -> "BinaryMetadata":
        """Deserialize metadata from bytes."""
        if len(data) < 2:
            return BinaryMetadata()
        
        length = struct.unpack(">H", data[:2])[0]
        if len(data) < 2 + length:
            return BinaryMetadata()
        
        json_bytes = data[2:2+length]
        obj = json.loads(json_bytes.decode("utf-8"))
        
        return BinaryMetadata(
            compression_algorithm=obj.get("compression_algorithm"),
            compression_level=obj.get("compression_level"),
            encryption_algorithm=obj.get("encryption_algorithm"),
            encryption_key_id=obj.get("encryption_key_id"),
            encryption_nonce=obj.get("encryption_nonce"),
            encryption_tag=obj.get("encryption_tag"),
            custom=obj.get("custom", {})
        )


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
    
    def generate(self, superbit_stream: SuperBitGroup) -> List[BinaryFrame]:
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
