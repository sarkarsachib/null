"""Optimization passes for the compiler."""

from abc import ABC, abstractmethod
from typing import List

from ..superbit.tokens import SuperBitToken, SuperBitGroup


class OptimizationPass(ABC):
    """Base class for optimization passes."""
    
    @abstractmethod
    def optimize(self, stream: SuperBitGroup) -> SuperBitGroup:
        """Apply optimization to a super-bit stream."""
        pass


class DeduplicationPass(OptimizationPass):
    """Remove duplicate consecutive operations."""
    
    def optimize(self, stream: SuperBitGroup) -> SuperBitGroup:
        """Remove duplicate consecutive LOAD_CONST operations."""
        tokens = []
        prev_token = None
        
        for token in stream.tokens:
            if prev_token and self._is_duplicate(prev_token, token):
                continue
            tokens.append(token)
            prev_token = token
        
        return SuperBitGroup(tokens=tokens)
    
    def _is_duplicate(self, token1: SuperBitToken, token2: SuperBitToken) -> bool:
        """Check if two tokens are duplicates."""
        if token1.symbol != token2.symbol:
            return False
        
        if token1.symbol == "LOAD_CONST":
            return token1.bits == token2.bits
        
        return False


class CompressionPass(OptimizationPass):
    """Compress constant operations."""
    
    def optimize(self, stream: SuperBitGroup) -> SuperBitGroup:
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
        
        return SuperBitGroup(tokens=tokens)
    
    def _is_constant_binary_op(self, tokens: List[SuperBitToken], idx: int) -> bool:
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
    
    def _fold_constants(self, tokens: List[SuperBitToken], idx: int) -> SuperBitToken:
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
        
        return SuperBitToken(symbol="LOAD_CONST", bits=result, bit_width=8)
