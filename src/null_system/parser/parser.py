"""Parser for Null-Lang syntax."""

from typing import List, Optional

from ..ast.nodes import (
    ASTNode,
    Program,
    SetStatement,
    LetBinding,
    BorrowExpr,
    LifetimeAnnotation,
    DropStatement,
    BinaryOp,
    PrintStatement,
    IfStatement,
    Identifier,
    Literal,
)
from .lexer import Token, TokenType


class ParseError(Exception):
    """Parse error exception."""
    pass


class Parser:
    """Parses tokens into an AST."""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = [t for t in tokens if t.type != TokenType.NEWLINE]
        self.position = 0
    
    def parse(self) -> Program:
        """Parse tokens into a Program AST."""
        statements = []
        
        while not self._is_at_end():
            if self._current().type == TokenType.EOF:
                break
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
        
        return Program(statements=statements)
    
    def _parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement."""
        token = self._current()
        
        if token.type == TokenType.SET:
            return self._parse_set_statement()
        elif token.type == TokenType.PRINT:
            return self._parse_print_statement()
        elif token.type == TokenType.IF:
            return self._parse_if_statement()
        elif token.type == TokenType.LET:
            return self._parse_let_binding()
        elif token.type == TokenType.DROP:
            return self._parse_drop_statement()
        elif token.type in [TokenType.ADD, TokenType.SUBTRACT, TokenType.MULTIPLY, TokenType.DIVIDE]:
            return self._parse_expression_statement()
        else:
            raise ParseError(f"Unexpected token: {token.value} at line {token.line}")
    
    def _parse_let_binding(self) -> LetBinding:
        """Parse Rust-like let binding: let x = 5 or let mut x = 5"""
        line = self._current().line
        self._consume(TokenType.LET, "Expected 'let'")
        
        # Check for mutability
        mutable = False
        if self._current().type == TokenType.MUT:
            self._advance()
            mutable = True
        
        # Parse pattern (for now, just identifier)
        pattern_token = self._consume(TokenType.IDENTIFIER, "Expected identifier in let binding")
        pattern = Identifier(name=pattern_token.value, line=pattern_token.line)
        
        self._consume(TokenType.EQUALS, "Expected '=' in let binding")
        
        value = self._parse_expression()
        
        return LetBinding(pattern=pattern, mutable=mutable, value=value, line=line)
    
    def _parse_drop_statement(self) -> DropStatement:
        """Parse explicit drop statement: drop variable"""
        line = self._current().line
        self._consume(TokenType.DROP, "Expected 'drop'")
        
        target = self._parse_expression()
        
        return DropStatement(target=target, line=line)
    
    def _parse_set_statement(self) -> SetStatement:
        """Parse: set x to 5"""
        line = self._current().line
        self._consume(TokenType.SET, "Expected 'set'")
        
        identifier_token = self._consume(TokenType.IDENTIFIER, "Expected identifier")
        identifier = identifier_token.value
        
        self._consume(TokenType.TO, "Expected 'to'")
        
        value = self._parse_expression()
        
        return SetStatement(identifier=identifier, value=value, line=line)
    
    def _parse_print_statement(self) -> PrintStatement:
        """Parse: print x"""
        line = self._current().line
        self._consume(TokenType.PRINT, "Expected 'print'")
        
        value = self._parse_expression()
        
        return PrintStatement(value=value, line=line)
    
    def _parse_if_statement(self) -> IfStatement:
        """Parse: if x is greater than 10 then print 'big' else print 'small'"""
        line = self._current().line
        self._consume(TokenType.IF, "Expected 'if'")
        
        condition = self._parse_comparison()
        
        self._consume(TokenType.THEN, "Expected 'then'")
        
        then_branch = [self._parse_statement()]
        
        else_branch = None
        if not self._is_at_end() and self._current().type == TokenType.ELSE:
            self._consume(TokenType.ELSE, "Expected 'else'")
            else_branch = [self._parse_statement()]
        
        return IfStatement(
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
            line=line
        )
    
    def _parse_expression_statement(self) -> BinaryOp:
        """Parse standalone expression that returns result."""
        return self._parse_expression()
    
    def _parse_expression(self) -> ASTNode:
        """Parse an expression."""
        return self._parse_comparison()
    
    def _parse_comparison(self) -> ASTNode:
        """Parse comparison: x is greater than 5"""
        left = self._parse_binary_op()
        
        if not self._is_at_end() and self._current().type == TokenType.IS:
            self._consume(TokenType.IS, "Expected 'is'")
            
            if self._current().type == TokenType.GREATER:
                self._consume(TokenType.GREATER, "Expected 'greater'")
                self._consume(TokenType.THAN, "Expected 'than'")
                right = self._parse_primary()
                return BinaryOp(op="greater_than", left=left, right=right)
            elif self._current().type == TokenType.LESS:
                self._consume(TokenType.LESS, "Expected 'less'")
                self._consume(TokenType.THAN, "Expected 'than'")
                right = self._parse_primary()
                return BinaryOp(op="less_than", left=left, right=right)
            elif self._current().type == TokenType.EQUALS:
                self._consume(TokenType.EQUALS, "Expected 'equals'")
                right = self._parse_primary()
                return BinaryOp(op="equals", left=left, right=right)
        
        return left
    
    def _parse_binary_op(self) -> ASTNode:
        """Parse binary operation: add x and 5"""
        if not self._is_at_end() and self._current().type in [
            TokenType.ADD, TokenType.SUBTRACT, TokenType.MULTIPLY, TokenType.DIVIDE
        ]:
            op_token = self._current()
            self._advance()
            
            left = self._parse_primary()
            
            self._consume(TokenType.AND, "Expected 'and'")
            
            right = self._parse_primary()
            
            op_map = {
                TokenType.ADD: "add",
                TokenType.SUBTRACT: "subtract",
                TokenType.MULTIPLY: "multiply",
                TokenType.DIVIDE: "divide",
            }
            
            return BinaryOp(
                op=op_map[op_token.type],
                left=left,
                right=right,
                line=op_token.line
            )
        
        return self._parse_primary()
    
    def _parse_primary(self) -> ASTNode:
        """Parse primary expression (literal, identifier, or borrow)."""
        token = self._current()
        
        if token.type == TokenType.NUMBER:
            self._advance()
            value = float(token.value) if '.' in token.value else int(token.value)
            return Literal(value=value, type="number", line=token.line)
        
        elif token.type == TokenType.STRING:
            self._advance()
            return Literal(value=token.value, type="string", line=token.line)
        
        elif token.type == TokenType.IDENTIFIER:
            self._advance()
            return Identifier(name=token.value, line=token.line)
        
        elif token.type == TokenType.BORROW:
            return self._parse_borrow_expression()
        
        else:
            raise ParseError(f"Unexpected token: {token.value} at line {token.line}")
    
    def _parse_borrow_expression(self) -> BorrowExpr:
        """Parse borrow expression: &var or &mut var"""
        line = self._current().line
        self._consume(TokenType.BORROW, "Expected '&'")
        
        # Check for mutability
        mutable = False
        if self._current().type == TokenType.MUT:
            self._advance()
            mutable = True
        
        # Parse the expression being borrowed
        expr = self._parse_primary()
        
        return BorrowExpr(expr=expr, mutable=mutable, line=line)
    
    def _current(self) -> Token:
        """Get the current token."""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return self.tokens[-1]
    
    def _advance(self) -> Token:
        """Move to the next token."""
        token = self._current()
        if self.position < len(self.tokens) - 1:
            self.position += 1
        return token
    
    def _consume(self, token_type: TokenType, message: str) -> Token:
        """Consume a token of the expected type."""
        if self._current().type == token_type:
            return self._advance()
        raise ParseError(f"{message} at line {self._current().line}")
    
    def _is_at_end(self) -> bool:
        """Check if we're at the end of tokens."""
        return self.position >= len(self.tokens)
