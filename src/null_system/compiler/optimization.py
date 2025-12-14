"""Optimization passes for the compiler."""

from abc import ABC, abstractmethod
from typing import List

from ..superbit.ir import SuperBitIRToken, SuperBitStream, SuperBitOpCode


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
    
    def _is_duplicate(self, token1: SuperBitIRToken, token2: SuperBitIRToken) -> bool:
        """Check if two tokens are duplicates."""
        if token1.symbol != token2.symbol:
            return False
        
        if token1.symbol == "LOAD_CONST":
            return token1.bits == token2.bits
        
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
    
    def _is_constant_binary_op(self, tokens: List[SuperBitIRToken], idx: int) -> bool:
        """Check if we have two constants followed by a binary op."""
        if idx + 2 >= len(tokens):
            return False
        
        return (
            tokens[idx].symbol == "LOAD_CONST" and
            tokens[idx + 1].symbol == "LOAD_CONST" and
            tokens[idx + 2].symbol in [
                "BINARY_ADD",
                "BINARY_SUB",
                "BINARY_MUL",
                "BINARY_DIV",
            ]
        )
    
    def _fold_constants(self, tokens: List[SuperBitIRToken], idx: int) -> SuperBitIRToken:
        """Fold constant binary operation."""
        left = tokens[idx].bits
        right = tokens[idx + 1].bits
        op = tokens[idx + 2].symbol
        
        if op == "BINARY_ADD":
            result = left + right
        elif op == "BINARY_SUB":
            result = left - right
        elif op == "BINARY_MUL":
            result = left * right
        elif op == "BINARY_DIV":
            result = left // right if right != 0 else 0
        else:
            result = left
        
        return SuperBitIRToken(SuperBitOpCode.LOAD_CONST, result)
