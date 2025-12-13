"""Optimization passes for the compiler."""

from abc import ABC, abstractmethod
from typing import List

from ..superbit.tokens import EnhancedSuperBitToken as SuperBitToken, SuperBitStream, SuperBitOpCode


class OptimizationPass(ABC):
    """Base class for optimization passes."""
    
    @abstractmethod
    def optimize(self, stream: SuperBitStream) -> SuperBitStream:
        """Apply optimization to a super-bit stream."""
        pass


class DeduplicationPass(OptimizationPass):
    """Remove duplicate consecutive operations."""
    
    def optimize(self, stream: SuperBitStream) -> SuperBitStream:
        """Remove duplicate consecutive LOAD_CONST operations."""
        tokens = []
        prev_token = None
        
        for token in stream.tokens:
            if prev_token and self._is_duplicate(prev_token, token):
                continue
            tokens.append(token)
            prev_token = token
        
        return SuperBitStream(tokens=tokens)
    
    def _is_duplicate(self, token1: SuperBitToken, token2: SuperBitToken) -> bool:
        """Check if two tokens are duplicates."""
        if token1.opcode != token2.opcode:
            return False
        
        if token1.opcode == SuperBitOpCode.LOAD_CONST:
            return token1.operand == token2.operand
        
        return False


class CompressionPass(OptimizationPass):
    """Compress constant operations."""
    
    def optimize(self, stream: SuperBitStream) -> SuperBitStream:
        """Fold constant expressions."""
        tokens = []
        i = 0
        
        while i < len(stream.tokens):
            if self._is_constant_binary_op(stream.tokens, i):
                result = self._fold_constants(stream.tokens, i)
                tokens.append(result)
                i += 3
            else:
                tokens.append(stream.tokens[i])
                i += 1
        
        return SuperBitStream(tokens=tokens)
    
    def _is_constant_binary_op(self, tokens: List[SuperBitToken], idx: int) -> bool:
        """Check if we have two constants followed by a binary op."""
        if idx + 2 >= len(tokens):
            return False
        
        return (
            tokens[idx].opcode == SuperBitOpCode.LOAD_CONST and
            tokens[idx + 1].opcode == SuperBitOpCode.LOAD_CONST and
            tokens[idx + 2].opcode in [
                SuperBitOpCode.BINARY_ADD,
                SuperBitOpCode.BINARY_SUB,
                SuperBitOpCode.BINARY_MUL,
                SuperBitOpCode.BINARY_DIV,
            ]
        )
    
    def _fold_constants(self, tokens: List[SuperBitToken], idx: int) -> SuperBitToken:
        """Fold constant binary operation."""
        left = tokens[idx].operand
        right = tokens[idx + 1].operand
        op = tokens[idx + 2].opcode
        
        if op == SuperBitOpCode.BINARY_ADD:
            result = left + right
        elif op == SuperBitOpCode.BINARY_SUB:
            result = left - right
        elif op == SuperBitOpCode.BINARY_MUL:
            result = left * right
        elif op == SuperBitOpCode.BINARY_DIV:
            result = left / right
        else:
            result = left
        
        return SuperBitToken(SuperBitOpCode.LOAD_CONST, result)
