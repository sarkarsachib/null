"""Advanced compression pass for the Null-Lang compiler.

Implements dictionary-based encoding and run-length packing over
the super-bit token stream with CPU vs. size heuristics.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum

from ..superbit.tokens import SuperBitStream, SuperBitToken, SuperBitOpCode
from ..compiler.optimization import OptimizationPass


class CompressionLevel(str, Enum):
    """Compression level settings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CompressionStats:
    """Statistics about compression results."""
    original_size: int
    compressed_size: int
    compression_ratio: float
    dictionary_entries: int
    rle_runs: int
    cpu_cycles_saved: int
    
    def __str__(self) -> str:
        return (
            f"CompressionStats(ratio={self.compression_ratio:.2%}, "
            f"dictionary={self.dictionary_entries}, "
            f"rle_runs={self.rle_runs})"
        )


class DictionaryEncoder:
    """Encodes tokens using a learned dictionary."""
    
    def __init__(self, max_dictionary_size: int = 256):
        """Initialize dictionary encoder.
        
        Args:
            max_dictionary_size: Maximum number of dictionary entries
        """
        self.max_dictionary_size = max_dictionary_size
        self.dictionary: Dict[str, int] = {}
        self.reverse_dictionary: Dict[int, str] = {}
        self.next_code = 256
    
    def learn_dictionary(self, tokens: List[SuperBitToken]) -> None:
        """Learn dictionary from tokens.
        
        Args:
            tokens: List of tokens to learn from
        """
        frequency: Dict[str, int] = {}
        
        for token in tokens:
            key = f"{token.symbol}:{token.operand}"
            frequency[key] = frequency.get(key, 0) + 1
        
        sorted_keys = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
        
        for key, _ in sorted_keys[:self.max_dictionary_size]:
            self.dictionary[key] = self.next_code
            self.reverse_dictionary[self.next_code] = key
            self.next_code += 1
    
    def encode_token(self, token: SuperBitToken) -> int:
        """Encode a token using dictionary.
        
        Args:
            token: Token to encode
            
        Returns:
            Dictionary code or -1 if not in dictionary
        """
        key = f"{token.symbol}:{token.operand}"
        return self.dictionary.get(key, -1)
    
    def decode_token(self, code: int) -> Optional[Tuple[str, Optional[str]]]:
        """Decode a dictionary code back to token info.
        
        Args:
            code: Dictionary code
            
        Returns:
            Tuple of (opcode, operand) or None if not found
        """
        key = self.reverse_dictionary.get(code)
        if key is None:
            return None
        
        parts = key.split(":", 1)
        if len(parts) == 2:
            return parts[0], parts[1] if parts[1] != "None" else None
        return parts[0], None


class RunLengthEncoder:
    """Performs run-length encoding on token sequences."""
    
    @staticmethod
    def encode(tokens: List[SuperBitToken]) -> List[Tuple[SuperBitToken, int]]:
        """Encode tokens with run-length encoding.
        
        Args:
            tokens: List of tokens
            
        Returns:
            List of (token, count) tuples
        """
        if not tokens:
            return []
        
        runs = []
        current_token = tokens[0]
        count = 1
        
        for token in tokens[1:]:
            if (token.opcode == current_token.opcode and
                token.operand == current_token.operand):
                count += 1
            else:
                runs.append((current_token, count))
                current_token = token
                count = 1
        
        runs.append((current_token, count))
        return runs
    
    @staticmethod
    def decode(runs: List[Tuple[SuperBitToken, int]]) -> List[SuperBitToken]:
        """Decode run-length encoded tokens.
        
        Args:
            runs: List of (token, count) tuples
            
        Returns:
            Expanded list of tokens
        """
        tokens = []
        for token, count in runs:
            tokens.extend([token] * count)
        return tokens


class AdvancedCompressionPass(OptimizationPass):
    """Advanced compression pass using dictionary and run-length encoding.
    
    Performs:
    1. Run-length encoding on consecutive identical tokens
    2. Dictionary-based encoding for common token patterns
    3. Heuristics for balancing compression vs. CPU cycles
    """
    
    def __init__(self, level: CompressionLevel = CompressionLevel.MEDIUM):
        """Initialize compression pass.
        
        Args:
            level: Compression level (LOW, MEDIUM, HIGH)
        """
        self.level = level
        self.stats: Optional[CompressionStats] = None
        self.dictionary_encoder = DictionaryEncoder()
        self.run_length_encoder = RunLengthEncoder()
    
    def optimize(self, stream: SuperBitStream) -> SuperBitStream:
        """Apply advanced compression to token stream.
        
        Args:
            stream: SuperBitStream to compress
            
        Returns:
            Compressed SuperBitStream
        """
        tokens = stream.tokens
        
        if not tokens:
            self.stats = CompressionStats(0, 0, 1.0, 0, 0, 0)
            return stream
        
        original_size = len(tokens)
        
        if self.level == CompressionLevel.LOW:
            compressed_tokens = self._compress_low(tokens)
        elif self.level == CompressionLevel.MEDIUM:
            compressed_tokens = self._compress_medium(tokens)
        else:
            compressed_tokens = self._compress_high(tokens)
        
        compressed_size = len(compressed_tokens)
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0
        
        self.stats = CompressionStats(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            dictionary_entries=len(self.dictionary_encoder.dictionary),
            rle_runs=0,
            cpu_cycles_saved=(original_size - compressed_size) * 4
        )
        
        return SuperBitStream(tokens=compressed_tokens, metadata=stream.metadata)
    
    def _compress_low(self, tokens: List[SuperBitToken]) -> List[SuperBitToken]:
        """Low compression: only run-length encoding.
        
        Args:
            tokens: Original tokens
            
        Returns:
            Compressed tokens
        """
        runs = self.run_length_encoder.encode(tokens)
        
        compressed = []
        for token, count in runs:
            if count > 1:
                compressed.append(SuperBitToken(
                    f"RLE:{token.opcode}",
                    operand=count
                ))
            else:
                compressed.append(token)
        
        return compressed
    
    def _compress_medium(self, tokens: List[SuperBitToken]) -> List[SuperBitToken]:
        """Medium compression: run-length + dictionary encoding.
        
        Args:
            tokens: Original tokens
            
        Returns:
            Compressed tokens
        """
        self.dictionary_encoder.learn_dictionary(tokens)
        
        compressed = []
        for token in tokens:
            dict_code = self.dictionary_encoder.encode_token(token)
            if dict_code >= 0:
                compressed.append(SuperBitToken("DICT", operand=dict_code))
            else:
                compressed.append(token)
        
        runs = self.run_length_encoder.encode(compressed)
        
        final = []
        for token, count in runs:
            if count > 1 and token.opcode in ["DICT", "LOAD_CONST"]:
                final.append(SuperBitToken(
                    f"RLE:{token.opcode}",
                    operand=(token.operand, count) if token.operand else count
                ))
            else:
                final.append(token)
        
        return final
    
    def _compress_high(self, tokens: List[SuperBitToken]) -> List[SuperBitToken]:
        """High compression: aggressive dictionary + RLE + pattern matching.
        
        Args:
            tokens: Original tokens
            
        Returns:
            Compressed tokens
        """
        self.dictionary_encoder.max_dictionary_size = 512
        self.dictionary_encoder.learn_dictionary(tokens)
        
        compressed = []
        for token in tokens:
            dict_code = self.dictionary_encoder.encode_token(token)
            if dict_code >= 0:
                compressed.append(SuperBitToken("DICT", operand=dict_code))
            else:
                compressed.append(token)
        
        runs = self.run_length_encoder.encode(compressed)
        
        final = []
        for token, count in runs:
            if count > 1:
                final.append(SuperBitToken(
                    f"RLE:{token.opcode}",
                    operand=(token.operand, count) if token.operand else count
                ))
            else:
                final.append(token)
        
        return final
    
    def get_stats(self) -> Optional[CompressionStats]:
        """Get statistics from last compression.
        
        Returns:
            CompressionStats or None if no compression performed
        """
        return self.stats
