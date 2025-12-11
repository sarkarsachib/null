"""Binary frame generator."""

from dataclasses import dataclass
from typing import List

from ..superbit.tokens import SuperBitStream


@dataclass
class BinaryFrame:
    """A binary frame containing compiled code."""
    header: bytes
    code: bytes
    constants: bytes
    
    def to_bytes(self) -> bytes:
        """Convert frame to bytes."""
        return self.header + self.code + self.constants
    
    def __len__(self) -> int:
        """Get the size of the binary frame."""
        return len(self.header) + len(self.code) + len(self.constants)


class BinaryGenerator:
    """Generates binary frames from super-bit streams."""
    
    MAGIC_NUMBER = b'NULL'
    VERSION = 1
    
    def generate(self, superbit_stream: SuperBitStream) -> List[BinaryFrame]:
        """Generate binary frames from a super-bit stream."""
        header = self._generate_header()
        code = superbit_stream.to_bytes()
        constants = self._generate_constants_section()
        
        frame = BinaryFrame(header=header, code=code, constants=constants)
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
