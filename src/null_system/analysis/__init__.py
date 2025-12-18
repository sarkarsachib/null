"""Analysis modules for the Null-Lang compiler."""

from .ownership import OwnershipAnalyzer, OwnershipError

__all__ = ['OwnershipAnalyzer', 'OwnershipError']