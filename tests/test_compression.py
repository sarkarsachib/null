"""Tests for advanced compression features."""

import pytest

from src.null_system.extensions.compression import (
    AdvancedCompressionPass,
    CompressionLevel,
    CompressionStats,
    DictionaryEncoder,
    RunLengthEncoder,
)
from src.null_system.superbit.tokens import SuperBitStream, SuperBitToken, SuperBitOpCode


class TestRunLengthEncoder:
    """Tests for RunLengthEncoder."""
    
    def test_encode_consecutive_tokens(self):
        """Test encoding consecutive identical tokens."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 5),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 5),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 5),
        ]
        
        runs = RunLengthEncoder.encode(tokens)
        
        assert len(runs) == 1
        assert runs[0][1] == 3
    
    def test_encode_mixed_tokens(self):
        """Test encoding mixed tokens."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 5),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 5),
            SuperBitToken(SuperBitOpCode.BINARY_ADD),
            SuperBitToken(SuperBitOpCode.BINARY_ADD),
            SuperBitToken(SuperBitOpCode.BINARY_ADD),
        ]
        
        runs = RunLengthEncoder.encode(tokens)
        
        assert len(runs) == 2
        assert runs[0][1] == 2
        assert runs[1][1] == 3
    
    def test_decode_runs(self):
        """Test decoding run-length encoded tokens."""
        runs = [
            (SuperBitToken(SuperBitOpCode.LOAD_CONST, 5), 3),
            (SuperBitToken(SuperBitOpCode.BINARY_ADD), 2),
        ]
        
        decoded = RunLengthEncoder.decode(runs)
        
        assert len(decoded) == 5
        assert decoded[0].operand == 5
        assert decoded[2].opcode == SuperBitOpCode.BINARY_ADD
    
    def test_encode_decode_roundtrip(self):
        """Test encode/decode roundtrip."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.LOAD_VAR, "x"),
            SuperBitToken(SuperBitOpCode.BINARY_ADD),
        ]
        
        runs = RunLengthEncoder.encode(tokens)
        decoded = RunLengthEncoder.decode(runs)
        
        assert len(decoded) == len(tokens)
        for orig, dec in zip(tokens, decoded):
            assert orig.opcode == dec.opcode
            assert orig.operand == dec.operand


class TestDictionaryEncoder:
    """Tests for DictionaryEncoder."""
    
    def test_learn_dictionary(self):
        """Test learning dictionary from tokens."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.BINARY_ADD),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
        ]
        
        encoder = DictionaryEncoder()
        encoder.learn_dictionary(tokens)
        
        assert len(encoder.dictionary) > 0
        assert "LOAD_CONST:42" in encoder.dictionary
    
    def test_encode_token(self):
        """Test encoding a token with dictionary."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.BINARY_ADD),
        ]
        
        encoder = DictionaryEncoder()
        encoder.learn_dictionary(tokens)
        
        code = encoder.encode_token(SuperBitToken(SuperBitOpCode.LOAD_CONST, 42))
        assert code >= 0
    
    def test_decode_token(self):
        """Test decoding a dictionary code."""
        tokens = [SuperBitToken(SuperBitOpCode.LOAD_CONST, 42)]
        
        encoder = DictionaryEncoder()
        encoder.learn_dictionary(tokens)
        
        code = encoder.encode_token(SuperBitToken(SuperBitOpCode.LOAD_CONST, 42))
        decoded = encoder.decode_token(code)
        
        assert decoded is not None
        assert decoded[0] == SuperBitOpCode.LOAD_CONST.value
    
    def test_token_not_in_dictionary(self):
        """Test encoding token not in dictionary."""
        encoder = DictionaryEncoder()
        encoder.learn_dictionary([SuperBitToken(SuperBitOpCode.LOAD_CONST, 42)])
        
        code = encoder.encode_token(SuperBitToken(SuperBitOpCode.BINARY_ADD))
        assert code == -1
    
    def test_max_dictionary_size(self):
        """Test dictionary respects max size."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, i) for i in range(500)
        ]
        
        encoder = DictionaryEncoder(max_dictionary_size=256)
        encoder.learn_dictionary(tokens)
        
        assert len(encoder.dictionary) <= 256


class TestAdvancedCompressionPass:
    """Tests for AdvancedCompressionPass."""
    
    def test_low_compression(self):
        """Test low compression level."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 5),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 5),
            SuperBitToken(SuperBitOpCode.BINARY_ADD),
        ]
        stream = SuperBitStream(tokens=tokens)
        
        pass_obj = AdvancedCompressionPass(level=CompressionLevel.LOW)
        compressed = pass_obj.optimize(stream)
        
        assert compressed is not None
        assert len(compressed.tokens) <= len(tokens)
        assert pass_obj.stats is not None
    
    def test_medium_compression(self):
        """Test medium compression level."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.BINARY_ADD),
        ]
        stream = SuperBitStream(tokens=tokens)
        
        pass_obj = AdvancedCompressionPass(level=CompressionLevel.MEDIUM)
        compressed = pass_obj.optimize(stream)
        
        assert compressed is not None
        assert pass_obj.stats is not None
        assert pass_obj.stats.compression_ratio > 0
    
    def test_high_compression(self):
        """Test high compression level."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, i % 10) for i in range(100)
        ]
        stream = SuperBitStream(tokens=tokens)
        
        pass_obj = AdvancedCompressionPass(level=CompressionLevel.HIGH)
        compressed = pass_obj.optimize(stream)
        
        assert compressed is not None
        assert len(compressed.tokens) < len(tokens)
        assert pass_obj.stats.compression_ratio < 1.0
    
    def test_empty_stream(self):
        """Test compression of empty stream."""
        stream = SuperBitStream(tokens=[])
        
        pass_obj = AdvancedCompressionPass()
        compressed = pass_obj.optimize(stream)
        
        assert len(compressed.tokens) == 0
        assert pass_obj.stats.compression_ratio == 1.0
    
    def test_single_token_stream(self):
        """Test compression of single token."""
        tokens = [SuperBitToken(SuperBitOpCode.LOAD_CONST, 42)]
        stream = SuperBitStream(tokens=tokens)
        
        pass_obj = AdvancedCompressionPass()
        compressed = pass_obj.optimize(stream)
        
        assert len(compressed.tokens) >= 1
    
    def test_compression_stats(self):
        """Test compression statistics calculation."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, i) for i in range(50)
        ]
        stream = SuperBitStream(tokens=tokens)
        
        pass_obj = AdvancedCompressionPass(level=CompressionLevel.HIGH)
        compressed = pass_obj.optimize(stream)
        
        stats = pass_obj.get_stats()
        assert stats is not None
        assert stats.original_size == 50
        assert stats.compressed_size > 0
        assert stats.compression_ratio > 0
        assert stats.cpu_cycles_saved >= 0
    
    def test_compression_preserves_stream_type(self):
        """Test that compression returns a valid SuperBitStream."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.LOAD_VAR, "x"),
        ]
        stream = SuperBitStream(tokens=tokens)
        
        pass_obj = AdvancedCompressionPass()
        compressed = pass_obj.optimize(stream)
        
        assert isinstance(compressed, SuperBitStream)
        assert hasattr(compressed, 'tokens')
        assert isinstance(compressed.tokens, list)
    
    def test_compression_stats_str(self):
        """Test compression stats string representation."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, i) for i in range(10)
        ]
        stream = SuperBitStream(tokens=tokens)
        
        pass_obj = AdvancedCompressionPass()
        pass_obj.optimize(stream)
        
        stats_str = str(pass_obj.stats)
        assert "ratio=" in stats_str
        assert "dictionary=" in stats_str
        assert "rle_runs=" in stats_str
    
    def test_no_stats_before_optimization(self):
        """Test that stats is None before optimization."""
        pass_obj = AdvancedCompressionPass()
        assert pass_obj.stats is None
    
    def test_compression_ratio_calculation(self):
        """Test compression ratio is correctly calculated."""
        tokens = [
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
            SuperBitToken(SuperBitOpCode.LOAD_CONST, 42),
        ]
        stream = SuperBitStream(tokens=tokens)
        
        pass_obj = AdvancedCompressionPass(level=CompressionLevel.LOW)
        compressed = pass_obj.optimize(stream)
        
        expected_ratio = len(compressed.tokens) / len(tokens)
        assert abs(pass_obj.stats.compression_ratio - expected_ratio) < 0.01
