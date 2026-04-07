import re
import math
import sys
import argparse
import time
import random
import ast
import operator
from enum import Enum, auto
from PIL import Image, ImageDraw, ImageFont, ImageChops

class EGLValue:
    def __init__(self, val):
        if isinstance(val, EGLValue): self.val = val.val
        elif isinstance(val, bool): self.val = 1 if val else 0
        else: self.val = val
    def __add__(self, other):
        v1, v2 = self.val, getattr(other, 'val', other)
        if isinstance(v1, str) or isinstance(v2, str): return EGLValue(str(v1) + str(v2))
        try: return EGLValue(v1 + v2)
        except: return EGLValue(str(v1) + str(v2))
    def __radd__(self, other):
        v1, v2 = getattr(other, 'val', other), self.val
        if isinstance(v1, str) or isinstance(v2, str): return EGLValue(str(v1) + str(v2))
        try: return EGLValue(v1 + v2)
        except: return EGLValue(str(v1) + str(v2))
    def __sub__(self, other): return EGLValue(float(self.val) - float(getattr(other, 'val', other)))
    def __rsub__(self, other): return EGLValue(float(getattr(other, 'val', other)) - float(self.val))
    def __mul__(self, other): return EGLValue(float(self.val) * float(getattr(other, 'val', other)))
    def __rmul__(self, other): return EGLValue(float(getattr(other, 'val', other)) * float(self.val))
    def __truediv__(self, other):
        try: return EGLValue(float(self.val) / float(getattr(other, 'val', other)))
        except ZeroDivisionError: return EGLValue(0)
    def __rtruediv__(self, other):
        try: return EGLValue(float(getattr(other, 'val', other)) / float(self.val))
        except ZeroDivisionError: return EGLValue(0)
    def __mod__(self, other):
        try: return EGLValue(float(self.val) % float(getattr(other, 'val', other)))
        except ZeroDivisionError: return EGLValue(0)
    def __rmod__(self, other):
        try: return EGLValue(float(getattr(other, 'val', other)) % float(self.val))
        except ZeroDivisionError: return EGLValue(0)
    def __xor__(self, other): return EGLValue(int(float(self.val)) ^ int(float(getattr(other, 'val', other))))
    def __and__(self, other): return EGLValue(int(float(self.val)) & int(float(getattr(other, 'val', other))))
    def __or__(self, other): return EGLValue(int(float(self.val)) | int(float(getattr(other, 'val', other))))
    def __neg__(self):
        try: return EGLValue(-float(self.val))
        except: return EGLValue(0)
    def __pos__(self):
        try: return EGLValue(float(self.val))
        except: return EGLValue(self.val)
    def _coerce(self, other):
        v1, v2 = self.val, getattr(other, 'val', other)
        if isinstance(v1, (int, float)) and isinstance(v2, str):
            try: v2 = float(v2)
            except: pass
        elif isinstance(v1, str) and isinstance(v2, (int, float)):
            try: v1 = float(v1)
            except: pass
        return v1, v2
    def __lt__(self, other):
        v1, v2 = self._coerce(other)
        try: return v1 < v2
        except: return str(v1) < str(v2)
    def __le__(self, other):
        v1, v2 = self._coerce(other)
        try: return v1 <= v2
        except: return str(v1) <= str(v2)
    def __gt__(self, other):
        v1, v2 = self._coerce(other)
        try: return v1 > v2
        except: return str(v1) > str(v2)
    def __ge__(self, other):
        v1, v2 = self._coerce(other)
        try: return v1 >= v2
        except: return str(v1) >= str(v2)
    def __eq__(self, other):
        v1, v2 = self._coerce(other)
        return v1 == v2
    def __ne__(self, other):
        v1, v2 = self._coerce(other)
        return v1 != v2
    def __str__(self):
        if isinstance(self.val, float) and self.val.is_integer(): return str(int(self.val))
        return str(self.val)
    def __repr__(self): return repr(self.val)
    def __int__(self): return int(float(self.val))
    def __float__(self): return float(self.val)

class TokenType(Enum):
    LPAREN = auto(); RPAREN = auto(); LBRACE = auto(); RBRACE = auto()
    COMMA = auto(); SEMICOLON = auto(); EQUAL = auto(); AT = auto()
    QUESTION = auto(); COLON = auto(); BANG = auto(); GT = auto(); LT = auto()
    LBRACKET = auto(); RBRACKET = auto()
    PLUS = auto(); MINUS = auto(); STAR = auto(); SLASH = auto(); MOD = auto(); CARET = auto()
    AND = auto(); OR = auto(); EQ = auto(); NE = auto(); GE = auto(); LE = auto()
    IDENTIFIER = auto(); VARIABLE = auto(); NUMBER = auto(); STRING = auto()
    EOF = auto()

class Token:
    def __init__(self, type, value, line, col):
        self.type, self.value, self.line, self.col = type, value, line, col
    def __repr__(self): return f"Token({self.type}, {repr(self.value)}, {self.line}:{self.col})"

class ASTNode:
    def __init__(self, line=0, col=0): self.line, self.col = line, col
class BinOpNode(ASTNode):
    def __init__(self, left, op, right, line=0, col=0): super().__init__(line, col); self.left, self.op, self.right = left, op, right
class UnaryOpNode(ASTNode):
    def __init__(self, op, operand, line=0, col=0): super().__init__(line, col); self.op, self.operand = op, operand
class LiteralNode(ASTNode):
    def __init__(self, value, line=0, col=0): super().__init__(line, col); self.value = value
class VarNode(ASTNode):
    def __init__(self, name, line=0, col=0): super().__init__(line, col); self.name = name
class CallNode(ASTNode):
    def __init__(self, name, args, line=0, col=0): super().__init__(line, col); self.name, self.args = name, args
class AssignNode(ASTNode):
    def __init__(self, name, expr, line=0, col=0): super().__init__(line, col); self.name, self.expr = name, expr
class CommandNode(ASTNode):
    def __init__(self, name, args, line=0, col=0): super().__init__(line, col); self.name, self.args = name, args
class IfNode(ASTNode):
    def __init__(self, cond, true_block, false_block=None, line=0, col=0): super().__init__(line, col); self.cond, self.true_block, self.false_block = cond, true_block, false_block
class WhileNode(ASTNode):
    def __init__(self, cond, block, line=0, col=0): super().__init__(line, col); self.cond, self.block = cond, block
class ForNode(ASTNode):
    def __init__(self, var, start, end, step, block, line=0, col=0): super().__init__(line, col); self.var, self.start, self.end, self.step, self.block = var, start, end, step, block
class FuncDefNode(ASTNode):
    def __init__(self, name, params, block, line=0, col=0): super().__init__(line, col); self.name, self.params, self.block = name, params, block
class BlockNode(ASTNode):
    def __init__(self, statements, line=0, col=0): super().__init__(line, col); self.statements = statements

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens; self.pos = 0
    def peek(self): return self.tokens[self.pos]
    def advance(self):
        token = self.tokens[self.pos]; self.pos += 1; return token
    def match(self, type):
        if self.peek().type == type: return self.advance()
        return None
    def expect(self, type):
        token = self.match(type)
        if not token: raise SyntaxError(f"Expected {type}, got {self.peek().type} at {self.peek().line}:{self.peek().col}")
        return token
    def parse_program(self):
        statements = []
        start_line, start_col = self.peek().line, self.peek().col
        while self.peek().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt: statements.append(stmt)
            while self.match(TokenType.SEMICOLON): pass
        return BlockNode(statements, start_line, start_col)
    def parse_statement(self):
        token = self.peek()
        line, col = token.line, token.col
        if token.type == TokenType.VARIABLE:
            name = self.advance().value; self.expect(TokenType.EQUAL); expr = self.parse_expression(); return AssignNode(name, expr, line, col)
        elif token.type == TokenType.COLON:
            self.advance()
            if self.peek().type == TokenType.IDENTIFIER:
                name = self.advance().value; self.expect(TokenType.LPAREN)
                params = []
                if self.peek().type != TokenType.RPAREN:
                    params.append(self.advance().value)
                    while self.match(TokenType.COMMA): params.append(self.advance().value)
                self.expect(TokenType.RPAREN); self.expect(TokenType.LBRACE); block = self.parse_block(); return FuncDefNode(name, params, block, line, col)
            return None
        elif token.type == TokenType.QUESTION:
            self.advance(); self.expect(TokenType.LPAREN); cond = self.parse_expression(); self.expect(TokenType.RPAREN); self.expect(TokenType.LBRACE); true_block = self.parse_block()
            false_block = None
            if self.match(TokenType.COLON):
                if self.peek().type == TokenType.LBRACE: self.advance(); false_block = self.parse_block()
            return IfNode(cond, true_block, false_block, line, col)
        elif token.type == TokenType.IDENTIFIER and token.value == "WH":
            self.advance(); self.expect(TokenType.LPAREN); cond = self.parse_expression(); self.expect(TokenType.RPAREN); self.expect(TokenType.LBRACE); block = self.parse_block(); return WhileNode(cond, block, line, col)
        elif token.type == TokenType.AT:
            self.advance(); self.expect(TokenType.LPAREN); var = self.expect(TokenType.VARIABLE).value; self.expect(TokenType.COMMA); start = self.parse_expression()
            self.expect(TokenType.COMMA); end = self.parse_expression(); self.expect(TokenType.COMMA); step = self.parse_expression(); self.expect(TokenType.RPAREN); self.expect(TokenType.LBRACE); block = self.parse_block()
            return ForNode(var, start, end, step, block, line, col)
        elif token.type == TokenType.BANG:
            self.advance(); name = self.expect(TokenType.IDENTIFIER).value; args = []
            if self.match(TokenType.LPAREN): args = self.parse_args(); self.expect(TokenType.RPAREN)
            return CallNode(name, args, line, col)
        elif token.type in [TokenType.IDENTIFIER, TokenType.GT, TokenType.LT, TokenType.STAR, TokenType.LBRACKET, TokenType.RBRACKET]:
            name = self.advance().value; args = []
            if self.match(TokenType.LPAREN): args = self.parse_args(); self.expect(TokenType.RPAREN)
            elif name in ['>', '<', '*', '[', ']'] and self.peek().type in [TokenType.NUMBER, TokenType.STRING, TokenType.VARIABLE, TokenType.IDENTIFIER, TokenType.LPAREN]:
                args = [self.parse_expression()]
            return CommandNode(name, args, line, col)
        elif self.match(TokenType.SEMICOLON): return None
        else: raise SyntaxError(f"Unexpected token {token} at statement start")
    def parse_block(self):
        statements = []
        start_line, start_col = self.peek().line, self.peek().col
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            stmt = self.parse_statement()
            if stmt: statements.append(stmt)
            while self.match(TokenType.SEMICOLON): pass
        self.expect(TokenType.RBRACE); return BlockNode(statements, start_line, start_col)
    def parse_args(self):
        args = []
        if self.peek().type != TokenType.RPAREN:
            args.append(self.parse_expression())
            while self.match(TokenType.COMMA) or self.match(TokenType.SEMICOLON): args.append(self.parse_expression())
        return args
    def parse_expression(self): return self.parse_comparison()
    def parse_comparison(self):
        node = self.parse_arithmetic()
        while self.peek().type in [TokenType.EQ, TokenType.NE, TokenType.GE, TokenType.LE]:
            line, col = self.peek().line, self.peek().col
            op = self.advance().type; node = BinOpNode(node, op, self.parse_arithmetic(), line, col)
        while self.peek().type == TokenType.IDENTIFIER and self.peek().value in ['>', '<']:
            line, col = self.peek().line, self.peek().col
            op_val = self.advance().value
            op_type = TokenType.GT if op_val == '>' else TokenType.LT
            node = BinOpNode(node, op_type, self.parse_arithmetic(), line, col)
        return node
    def parse_arithmetic(self):
        node = self.parse_term()
        while self.peek().type in [TokenType.PLUS, TokenType.MINUS, TokenType.OR, TokenType.CARET]:
            line, col = self.peek().line, self.peek().col
            op = self.advance().type; node = BinOpNode(node, op, self.parse_term(), line, col)
        return node
    def parse_term(self):
        node = self.parse_factor()
        while self.peek().type in [TokenType.STAR, TokenType.SLASH, TokenType.MOD, TokenType.AND]:
            line, col = self.peek().line, self.peek().col
            op = self.advance().type; node = BinOpNode(node, op, self.parse_factor(), line, col)
        return node
    def parse_factor(self):
        token = self.peek()
        line, col = token.line, token.col
        if token.type == TokenType.PLUS: self.advance(); return UnaryOpNode(TokenType.PLUS, self.parse_factor(), line, col)
        if token.type == TokenType.MINUS: self.advance(); return UnaryOpNode(TokenType.MINUS, self.parse_factor(), line, col)
        return self.parse_primary()
    def parse_primary(self):
        token = self.peek()
        line, col = token.line, token.col
        token = self.advance()
        if token.type == TokenType.NUMBER or token.type == TokenType.STRING: return LiteralNode(token.value, line, col)
        elif token.type == TokenType.VARIABLE: return VarNode(token.value, line, col)
        elif token.type == TokenType.IDENTIFIER:
            if self.match(TokenType.LPAREN): args = self.parse_args(); self.expect(TokenType.RPAREN); return CallNode(token.value, args, line, col)
            return VarNode(token.value, line, col)
        elif token.type == TokenType.LPAREN: expr = self.parse_expression(); self.expect(TokenType.RPAREN); return expr
        raise SyntaxError(f"Unexpected token in expression: {token}")

class Lexer:
    def __init__(self, text):
        self.text = text; self.pos = 0; self.line = 1; self.col = 1
    def advance(self):
        char = self.text[self.pos]; self.pos += 1
        if char == '\n': self.line += 1; self.col = 1
        else: self.col += 1
        return char
    def peek(self): return self.text[self.pos] if self.pos < len(self.text) else None
    def get_tokens(self):
        tokens = []
        paren_depth = 0
        while self.pos < len(self.text):
            char = self.peek()
            if char.isspace():
                if char == '\n' and paren_depth == 0:
                    if tokens and tokens[-1].type not in [TokenType.SEMICOLON, TokenType.LBRACE, TokenType.COMMA]:
                        tokens.append(Token(TokenType.SEMICOLON, ";", self.line, self.col))
                self.advance()
            elif char == '#':
                while self.peek() and self.peek() != '\n': self.advance()
            elif char.isdigit(): tokens.append(self.read_number())
            elif char == '"' or char == "'": tokens.append(self.read_string(char))
            elif char == '$': tokens.append(self.read_variable())
            elif char.isalpha() or char == '_': tokens.append(self.read_identifier())
            elif char == '(':
                paren_depth += 1; tokens.append(Token(TokenType.LPAREN, self.advance(), self.line, self.col))
            elif char == ')':
                paren_depth = max(0, paren_depth - 1); tokens.append(Token(TokenType.RPAREN, self.advance(), self.line, self.col))
            elif char == '{': tokens.append(Token(TokenType.LBRACE, self.advance(), self.line, self.col))
            elif char == '}': tokens.append(Token(TokenType.RBRACE, self.advance(), self.line, self.col))
            elif char == '[':
                paren_depth += 1; tokens.append(Token(TokenType.LBRACKET, self.advance(), self.line, self.col))
            elif char == ']':
                paren_depth = max(0, paren_depth - 1); tokens.append(Token(TokenType.RBRACKET, self.advance(), self.line, self.col))
            elif char == ',': tokens.append(Token(TokenType.COMMA, self.advance(), self.line, self.col))
            elif char == ';': tokens.append(Token(TokenType.SEMICOLON, self.advance(), self.line, self.col))
            elif char == '=':
                line, col = self.line, self.col; self.advance()
                if self.peek() == '=': self.advance(); tokens.append(Token(TokenType.EQ, "==", line, col))
                else: tokens.append(Token(TokenType.EQUAL, "=", line, col))
            elif char == '!':
                line, col = self.line, self.col; self.advance()
                if self.peek() == '=': self.advance(); tokens.append(Token(TokenType.NE, "!=", line, col))
                else: tokens.append(Token(TokenType.BANG, "!", line, col))
            elif char == '>':
                line, col = self.line, self.col; self.advance()
                if self.peek() == '=': self.advance(); tokens.append(Token(TokenType.GE, ">=", line, col))
                else: tokens.append(Token(TokenType.IDENTIFIER, ">", line, col))
            elif char == '<':
                line, col = self.line, self.col; self.advance()
                if self.peek() == '=': self.advance(); tokens.append(Token(TokenType.LE, "<=", line, col))
                else: tokens.append(Token(TokenType.IDENTIFIER, "<", line, col))
            elif char == '+': tokens.append(Token(TokenType.PLUS, self.advance(), self.line, self.col))
            elif char == '-': tokens.append(Token(TokenType.MINUS, self.advance(), self.line, self.col))
            elif char == '*': tokens.append(Token(TokenType.STAR, self.advance(), self.line, self.col))
            elif char == '/': tokens.append(Token(TokenType.SLASH, self.advance(), self.line, self.col))
            elif char == '%': tokens.append(Token(TokenType.MOD, self.advance(), self.line, self.col))
            elif char == '^': tokens.append(Token(TokenType.CARET, self.advance(), self.line, self.col))
            elif char == '&': tokens.append(Token(TokenType.AND, self.advance(), self.line, self.col))
            elif char == '|': tokens.append(Token(TokenType.OR, self.advance(), self.line, self.col))
            elif char == '?': tokens.append(Token(TokenType.QUESTION, self.advance(), self.line, self.col))
            elif char == ':': tokens.append(Token(TokenType.COLON, self.advance(), self.line, self.col))
            elif char == '@': tokens.append(Token(TokenType.AT, self.advance(), self.line, self.col))
            else: raise SyntaxError(f"Unexpected character '{char}' at {self.line}:{self.col}")
        tokens.append(Token(TokenType.EOF, None, self.line, self.col))
        return tokens
    def read_number(self):
        res = ""; line, col = self.line, self.col
        while self.peek() and (self.peek().isdigit() or self.peek() == '.'): res += self.advance()
        return Token(TokenType.NUMBER, float(res) if '.' in res else int(res), line, col)
    def read_string(self, quote):
        res = ""; line, col = self.line, self.col; self.advance()
        while self.peek() and self.peek() != quote: res += self.advance()
        self.advance(); return Token(TokenType.STRING, res, line, col)
    def read_variable(self):
        res = "$"; line, col = self.line, self.col; self.advance()
        while self.peek() and (self.peek().isalnum() or self.peek() == '_'): res += self.advance()
        return Token(TokenType.VARIABLE, res, line, col)
    def read_identifier(self):
        res = ""; line, col = self.line, self.col
        while self.peek() and (self.peek().isalnum() or self.peek() == '_'): res += self.advance()
        if not res and self.peek() in ['>', '<', '*', '[', ']']: res = self.advance()
        return Token(TokenType.IDENTIFIER, res, line, col)

class EGLInterpreter:
    def __init__(self, initial_vars=None, serial_in=None):
        self.globals = {"$pi": math.pi, "$e": math.e, "$last_key": "", "$last_key_src": "", "$result": 0}
        if initial_vars:
            for k, v in initial_vars.items():
                self.globals[k if k.startswith('$') else '$'+k] = v
        self.scopes = []
        self.functions = {}
        self.arrays = {}
        self.hit_zones = []
        self.event_queue = []
        self.key_states = {}
        self.palette = ["black"] * 256
        self.state_stack = []
        self.images = {"main": None}
        self.draws = {"main": None}
        self.front_buffer = None
        self.active_surface = "main"
        self.pos = (0, 0)
        self.stroke_color = "black"
        self.stroke_width = 1
        self.fill_color = None
        self.clip = None
        self.target_fps = 0
        self.serial_in = serial_in if serial_in else []
        self.serial_out = []
        self.start_time = time.time()
        self._init_builtins()

    def _init_builtins(self):
        self.op_map = {
            TokenType.PLUS: operator.add, TokenType.MINUS: operator.sub,
            TokenType.STAR: operator.mul, TokenType.SLASH: operator.truediv,
            TokenType.MOD: operator.mod, TokenType.CARET: operator.xor,
            TokenType.AND: operator.and_, TokenType.OR: operator.or_,
            TokenType.EQ: operator.eq, TokenType.NE: operator.ne,
            TokenType.LT: operator.lt, TokenType.LE: operator.le,
            TokenType.GT: operator.gt, TokenType.GE: operator.ge
        }
        self.builtins = {
            "cos": lambda x: math.cos(float(EGLValue(x))), "sin": lambda x: math.sin(float(EGLValue(x))),
            "tan": lambda x: math.tan(float(EGLValue(x))), "sqrt": lambda x: math.sqrt(float(EGLValue(x))),
            "abs": lambda x: abs(float(EGLValue(x))), "min": lambda a, b: min(float(EGLValue(a)), float(EGLValue(b))),
            "max": lambda a, b: max(float(EGLValue(a)), float(EGLValue(b))), "pow": lambda a, b: pow(float(EGLValue(a)), float(EGLValue(b))),
            "round": lambda x: round(float(EGLValue(x))), "len": lambda x: len(str(EGLValue(x))),
            "int": lambda x: int(float(EGLValue(x))), "float": lambda x: float(EGLValue(x)), "str": lambda x: str(EGLValue(x)),
            "hex": lambda x: hex(int(float(EGLValue(x)))), "zfill": lambda s, n: str(EGLValue(s)).zfill(int(float(EGLValue(n)))),
            "ST": lambda s, start, length=None: str(EGLValue(s))[int(float(EGLValue(start))):int(float(EGLValue(start)))+int(float(EGLValue(length))) if length is not None else None],
            "KS": lambda k: 1 if self.key_states.get(str(EGLValue(k))) else 0,
            "MS": lambda: int((time.time() - self.start_time) * 1000),
            "RN": lambda a, b: random.randint(int(float(EGLValue(a))), int(float(EGLValue(b)))),
            "HC": lambda x1, y1, w1, h1, x2, y2, w2, h2: 1 if (float(EGLValue(x1)) < float(EGLValue(x2)) + float(EGLValue(w2)) and float(EGLValue(x1)) + float(EGLValue(w1)) > float(EGLValue(x2)) and float(y1) < float(y2) + float(h2) and float(y1) + float(h1) > float(y2)) else 0,
            "MPX": lambda: self.globals.get("$last_mouse_x", 0),
            "MPY": lambda: self.globals.get("$last_mouse_y", 0)
        }

    def set_var(self, name, val):
        v = val.val if isinstance(val, EGLValue) else val
        if name.startswith('$'):
            self.globals[name] = v
            for scope in self.scopes:
                if name in scope: scope[name] = v
            return
        if self.scopes:
            for scope in reversed(self.scopes):
                if name in scope:
                    scope[name] = v
                    return
            self.scopes[-1][name] = v
        else:
            self.globals[name] = v

    def get_var(self, name):
        if self.scopes:
            for scope in reversed(self.scopes):
                if name in scope: return scope[name]
        if name in self.globals: return self.globals[name]
        if not str(name).startswith('$'): return name
        return 0

    def visit(self, node):
        try:
            if isinstance(node, BlockNode):
                res = None
                for stmt in node.statements: res = self.visit(stmt)
                return res
            elif isinstance(node, AssignNode):
                val = self.visit(node.expr)
                self.set_var(node.name, val); return val
            elif isinstance(node, CommandNode):
                args = [self.visit(arg) for arg in node.args]
                return self.run_cmd(node.name, args)
            elif isinstance(node, CallNode):
                args = [self.visit(arg) for arg in node.args]
                if node.name in self.builtins:
                    res = self.builtins[node.name](*args)
                    return EGLValue(res)
                elif node.name in self.functions:
                    params, body = self.functions[node.name]
                    scope = {p: (a.val if isinstance(a, EGLValue) else a) for p, a in zip(params, args)}
                    self.scopes.append(scope)
                    self.visit(body)
                    local = self.scopes.pop()
                    res = local.get("$result", 0)
                    if "$result" in self.globals: res = self.globals["$result"]
                    return EGLValue(res)
                else: raise NameError(f"Undefined function '{node.name}'")
            elif isinstance(node, IfNode):
                cond = self.visit(node.cond)
                if isinstance(cond, EGLValue): cond = cond.val
                if cond and cond != "0" and cond != 0: return self.visit(node.true_block)
                elif node.false_block: return self.visit(node.false_block)
            elif isinstance(node, WhileNode):
                res = None
                while True:
                    cond = self.visit(node.cond)
                    if isinstance(cond, EGLValue): cond = cond.val
                    if not cond or cond == "0" or cond == 0: break
                    res = self.visit(node.block)
                return res
            elif isinstance(node, ForNode):
                start = float(EGLValue(self.visit(node.start)))
                end = float(EGLValue(self.visit(node.end)))
                step = float(EGLValue(self.visit(node.step)))
                curr = start; res = None
                while (curr <= end if step > 0 else curr >= end):
                    self.set_var(node.var, curr)
                    res = self.visit(node.block)
                    curr += step
                return res
            elif isinstance(node, FuncDefNode):
                self.functions[node.name] = (node.params, node.block)
            elif isinstance(node, BinOpNode):
                v1, v2 = self.visit(node.left), self.visit(node.right)
                res = self.op_map[node.op](EGLValue(v1), EGLValue(v2))
                if node.op in [TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.LE, TokenType.GT, TokenType.GE]:
                    return 1 if res else 0
                return res.val if isinstance(res, EGLValue) else res
            elif isinstance(node, UnaryOpNode):
                val = EGLValue(self.visit(node.operand))
                if node.op == TokenType.MINUS: return (-val).val
                return val.val
            elif isinstance(node, LiteralNode): return node.value
            elif isinstance(node, VarNode): return self.get_var(node.name)
        except Exception as e:
            if node.line: print(f"RUNTIME ERROR at {node.line}:{node.col}: {e}")
            else: print(f"RUNTIME ERROR: {e}")
            raise e
        return None

    def eval_expr(self, expr_str):
        if isinstance(expr_str, (int, float, EGLValue)): return EGLValue(expr_str)
        if not expr_str: return EGLValue(0)
        try:
            lexer = Lexer(str(expr_str))
            tokens = lexer.get_tokens()
            parser = Parser(tokens)
            node = parser.parse_expression()
            return EGLValue(self.visit(node))
        except Exception: return EGLValue(str(expr_str))

    def _get_rgba(self, c):
        if isinstance(c, (int, float)):
            idx = int(c) % 256
            return self._get_rgba(self.palette[idx])
        cv = str(c)
        if cv == "None": return (0,0,0,0)
        if cv.startswith('#'):
            if len(cv) == 7: return tuple(int(cv[i:i+2], 16) for i in (1, 3, 5)) + (255,)
            if len(cv) == 9: return tuple(int(cv[i:i+2], 16) for i in (1, 3, 5, 7))
        colors = {"red":(255,0,0,255), "blue":(0,0,255,255), "green":(0,255,0,255), "black":(0,0,0,255), "white":(255,255,255,255), "gray":(128,128,128,255), "yellow":(255,255,0,255)}
        res = colors.get(cv.lower())
        if res: return res
        try:
            from PIL import ImageColor
            rgb = ImageColor.getrgb(cv)
            return rgb + (255,) if len(rgb) == 3 else rgb
        except Exception: return (255,255,255,255)

    def run_cmd(self, cmd, raw_args):
        if not raw_args and cmd in ['S', 'M', 'L', 'R', 'V', 'C', 'O', 'G', 'BX', 'AA', 'AV', 'AG', 'KP', 'KS', 'DX', 'LI', 'ST', 'FR', 'CP', 'HZ', 'MC', 'KC', 'B']:
             return
        args = [a.val if isinstance(a, EGLValue) else a for a in raw_args]
        sid = self.active_surface; draw = self.draws.get(sid); img = self.images.get(sid)
        try:
            if cmd == 'S':
                w, h = int(float(args[0])), int(float(args[1])); bg = args[2] if len(args) > 2 else "white"
                self.images["main"] = Image.new("RGBA", (w, h), self._get_rgba(bg)); self.draws["main"] = ImageDraw.Draw(self.images["main"])
                self.front_buffer = Image.new("RGBA", (w, h), self._get_rgba(bg)); self.active_surface = "main"; self.clip = None
            elif cmd == 'CL':
                if img: img.paste(self._get_rgba(args[0]), [0, 0, img.width, img.height])
            elif cmd == 'FB':
                if "main" in self.images and self.front_buffer: self.front_buffer.paste(self.images["main"])
                if self.target_fps > 0: time.sleep(1.0 / self.target_fps)
            elif cmd == 'FR': self.target_fps = int(float(args[0]))
            elif cmd == 'CP': self.palette[int(float(args[0])) % 256] = args[1]
            elif cmd == 'P':
                id = str(args[0])
                if len(args) >= 3:
                    w, h = int(float(args[1])), int(float(args[2]))
                    self.images[id] = Image.new("RGBA", (w, h), (0,0,0,0)); self.draws[id] = ImageDraw.Draw(self.images[id])
                self.active_surface = id; self.clip = None
            elif cmd == 'DX':
                id, dx, dy = str(args[0]), float(args[1]), float(args[2])
                angle, scale, alpha = (float(args[i]) if len(args) > i else d for i, d in [(3,0), (4,1.0), (5,1.0)])
                if id in self.images and img:
                    src = self.images[id]
                    if len(args) > 9: sx, sy, sw, sh = map(int, map(float, args[6:10])); src = src.crop((sx, sy, sx+sw, sy+sh))
                    if angle != 0: src = src.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
                    if scale != 1.0:
                        nw, nh = int(src.width * scale), int(src.height * scale)
                        if nw > 0 and nh > 0: src = src.resize((nw, nh), Image.Resampling.LANCZOS)
                    if alpha < 1.0:
                        a = src.getchannel('A').point(lambda p: p * alpha); src = src.copy(); src.putalpha(a)
                    img.paste(src, (int(dx - src.width/2), int(dy - src.height/2)), src)
            elif cmd == 'TM':
                tid, aid, cols, rows, tw, th = str(args[0]), str(args[1]), int(args[2]), int(args[3]), int(args[4]), int(args[5])
                ox, oy = (float(args[i]) if len(args) > i else 0 for i in (6, 7))
                if tid in self.images and aid in self.arrays and img:
                    ts = self.images[tid]; arr = self.arrays[aid]; ts_cols = ts.width // tw
                    for r in range(rows):
                        for c in range(cols):
                            idx = r * cols + c
                            if idx < len(arr):
                                tile_idx = int(float(getattr(arr[idx], 'val', arr[idx])))
                                if tile_idx >= 0:
                                    sx = (tile_idx % ts_cols) * tw; sy = (tile_idx // ts_cols) * th
                                    img.paste(ts.crop((sx, sy, sx+tw, sy+th)), (int(c*tw - ox), int(r*th - oy)))
            elif cmd == 'HC':
                x1, y1, w1, h1, x2, y2, w2, h2 = map(float, args[:8]); res = 1 if (x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2) else 0; self.set_var("$result", res)
            elif cmd == 'RN': self.set_var("$result", random.randint(int(args[0]), int(args[1])))
            elif cmd == 'SR': random.seed(int(args[0]))
            elif cmd == 'MS': self.set_var("$result", int((time.time() - self.start_time) * 1000))
            elif cmd == 'LI':
                try: self.images[str(args[0])] = Image.open(str(args[1])).convert("RGBA"); self.draws[str(args[0])] = ImageDraw.Draw(self.images[str(args[0])])
                except Exception: pass
            elif cmd == 'ST':
                s_val = str(args[0]); start = int(args[1])
                if len(args) > 2: self.set_var("$result", s_val[start:start+int(args[2])])
                else: self.set_var("$result", s_val[start:])
            elif cmd == 'LD':
                if len(args) >= 6:
                    sid, lx, ly, lw, lh, ldata = str(args[0]), int(float(args[1])), int(float(args[2])), int(float(args[3])), int(float(args[4])), str(args[5])
                    if sid in self.images:
                        target = self.images[sid]
                        pixels = []
                        for i in range(0, len(ldata), 2):
                            try:
                                p_idx = int(ldata[i:i+2], 16)
                                pixels.append(self._get_rgba(p_idx))
                            except: pixels.append((0,0,0,0))
                        if len(pixels) >= lw * lh:
                            patch = Image.new("RGBA", (lw, lh))
                            patch.putdata(pixels[:lw*lh])
                            target.paste(patch, (lx, ly))
            elif cmd == 'KS': self.set_var("$result", 1 if self.key_states.get(str(args[0])) else 0)
            elif cmd == 'KP': self.key_states[str(args[0])] = int(float(args[1]))
            elif cmd == 'HZ':
                if not args: self.hit_zones = []
                elif len(args) >= 6:
                    zid = str(args[0])
                    coords = (float(args[1]), float(args[2]), float(args[3]), float(args[4]), str(args[5]))
                    for i, hz in enumerate(self.hit_zones):
                        if hz[0] == zid:
                            self.hit_zones[i] = (zid,) + coords
                            break
                    else: self.hit_zones.append((zid,) + coords)
            elif cmd == 'MC':
                self.set_var("$last_mouse_x", float(args[0]))
                self.set_var("$last_mouse_y", float(args[1]))
                self.event_queue.append(('MC', float(args[0]), float(args[1]), float(args[2])))
            elif cmd == 'KC': self.event_queue.append(('KC', str(args[0]), str(args[1])))
            elif cmd == 'DE':
                q = self.event_queue; self.event_queue = []
                for ev in q:
                    if ev[0] == 'MC':
                        ex, ey, eb = ev[1:]
                        for hz in reversed(self.hit_zones):
                            hzid, hx, hy, hw, hh, hf = hz
                            if hx <= ex <= hx+hw and hy <= ey <= hy+hh:
                                if hf in self.functions:
                                    self.set_var("$last_click_x", ex); self.set_var("$last_click_y", ey); self.set_var("$last_click_btn", eb)
                                    self.visit(self.functions[hf][1]); break
                    elif ev[0] == 'KC':
                        esrc, ek = ev[1:]; self.set_var("$last_key", ek); self.set_var("$last_key_src", esrc)
                        if "ON_KEY" in self.functions: self.visit(self.functions["ON_KEY"][1])
            elif cmd == 'B':
                x, y, w, h = map(float, args[0:4]); c1, c2 = args[4], args[5]; dr = int(args[6]) if len(args) > 6 else 1
                if img:
                    base = Image.new('RGBA', (int(w), int(h)), (0,0,0,0)); d = ImageDraw.Draw(base); rgb1, rgb2 = self._get_rgba(c1), self._get_rgba(c2)
                    steps = int(w if dr == 0 else h)
                    for i in range(steps):
                        ratio = i / max(1, steps-1); curr_c = tuple(int(rgb1[j] + (rgb2[j] - rgb1[j]) * ratio) for j in range(4))
                        if dr == 0: d.line([(i, 0), (i, h)], fill=curr_c)
                        else: d.line([(0, i), (w, i)], fill=curr_c)
                    img.paste(base, (int(x), int(y)), base)
            elif cmd == 'BX':
                if len(args) >= 4: x, y, w, h = map(float, args[0:4])
                else: x, y = self.pos; w, h = map(float, args[0:2])
                if draw: draw.rectangle([x, y, x+w, y+h], fill=self._get_rgba(self.fill_color), outline=self._get_rgba(self.stroke_color), width=self.stroke_width)
            elif cmd == 'AA': self.arrays[str(args[0])] = [0] * int(float(args[1]))
            elif cmd == 'AV':
                aid, idx = str(args[0]), int(float(args[1]))
                if aid in self.arrays and 0 <= idx < len(self.arrays[aid]): self.arrays[aid][idx] = args[2]
            elif cmd == 'AG':
                aid, idx = str(args[0]), int(float(args[1]))
                if aid in self.arrays and 0 <= idx < len(self.arrays[aid]): self.set_var("$result", self.arrays[aid][idx])
                else: self.set_var("$result", 0)
            elif cmd == 'K':
                self.stroke_color = args[0]
                if len(args) > 1: self.stroke_width = int(float(args[1]))
            elif cmd == 'F': self.fill_color = args[0] if args[0] != "None" else None
            elif cmd == 'M': self.pos = (float(args[0]), float(args[1]))
            elif cmd == 'R': self.pos = (self.pos[0] + float(args[0]), self.pos[1] + float(args[1]))
            elif cmd == 'L':
                np = (float(args[0]), float(args[1]))
                if draw: draw.line([self.pos, np], fill=self._get_rgba(self.stroke_color), width=self.stroke_width)
                self.pos = np
            elif cmd == 'V':
                np = (self.pos[0] + float(args[0]), self.pos[1] + float(args[1]))
                if draw: draw.line([self.pos, np], fill=self._get_rgba(self.stroke_color), width=self.stroke_width)
                self.pos = np
            elif cmd == 'C':
                if args:
                    r = float(args[0]); b = [self.pos[0]-r, self.pos[1]-r, self.pos[0]+r, self.pos[1]+r]
                    if draw: draw.ellipse(b, fill=self._get_rgba(self.fill_color), outline=self._get_rgba(self.stroke_color), width=self.stroke_width)
            elif cmd == 'O':
                if len(args) >= 2:
                    rx, ry = float(args[0]), float(args[1]); b = [self.pos[0]-rx, self.pos[1]-ry, self.pos[0]+rx, self.pos[1]+ry]
                    if draw: draw.ellipse(b, fill=self._get_rgba(self.fill_color), outline=self._get_rgba(self.stroke_color), width=self.stroke_width)
            elif cmd == 'G':
                if len(args) >= 4:
                    pts = [(float(args[i]), float(args[i+1])) for i in range(0, len(args)-1, 2)]
                    if draw:
                        if self.fill_color and self.fill_color != "None": draw.polygon(pts, fill=self._get_rgba(self.fill_color), outline=self._get_rgba(self.stroke_color), width=self.stroke_width)
                        else: draw.line(pts + [pts[0]], fill=self._get_rgba(self.stroke_color), width=self.stroke_width)
            elif cmd == 'T':
                if draw:
                    try: f = ImageFont.load_default(); draw.text(self.pos, str(args[0]), fill=self._get_rgba(self.stroke_color), font=f)
                    except Exception: pass
            elif cmd == '>':
                if args:
                    msg = str(args[0]); self.serial_out.append(msg); sys.stdout.write("EGL_OUT: " + msg + "\n"); sys.stdout.flush()
            elif cmd == '<':
                vn = str(args[0]).strip('()$ '); val = self.serial_in.pop(0) if self.serial_in else 0; self.set_var('$' + vn, val)
            elif cmd == '[': self.state_stack.append((self.pos, self.stroke_color, self.stroke_width, self.fill_color, self.active_surface, self.clip))
            elif cmd == ']':
                if self.state_stack: self.pos, self.stroke_color, self.stroke_width, self.fill_color, self.active_surface, self.clip = self.state_stack.pop()
        except Exception as e: print(f"ERROR executing {cmd} with {args}: {e}")

    def run_code(self, code):
        if not isinstance(code, str):
            if isinstance(code, BlockNode): self.visit(code); return
            else: raise ValueError(f"run_code expects string or BlockNode, got {type(code)}")
        try:
            lexer = Lexer(code)
            tokens = lexer.get_tokens()
            parser = Parser(tokens)
            ast_root = parser.parse_program()
            self.visit(ast_root)
        except Exception as e:
            print(f"INTERPRETER ERROR: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="EGL script file")
    parser.add_argument("--vars", help="Initial variables")
    parser.add_argument("--serial-in", help="Serial input data")
    parser.add_argument("--events", help="Pre-load events")
    parser.add_argument("--output", default="output.png", help="Output PNG file")
    args = parser.parse_args()
    init_vars = {}
    if args.vars:
        for item in args.vars.split(','):
            try:
                k, v = item.split('='); init_vars[k] = float(v) if '.' in v or v.isnumeric() else v
            except Exception: pass
    ser_in = []
    if args.serial_in:
        for val in args.serial_in.split(','):
            try: ser_in.append(float(val) if '.' in val or val.isdigit() else val)
            except Exception: ser_in.append(val)
    it = EGLInterpreter(initial_vars=init_vars, serial_in=ser_in)
    if args.events:
        for ev_s in args.events.split(';'):
            pts = ev_s.split(',')
            if pts[0] == 'MC': it.event_queue.append(('MC', float(pts[1]), float(pts[2]), float(pts[3])))
            elif pts[0] == 'KC': it.event_queue.append(('KC', str(pts[1]), str(pts[2])))
            elif pts[0] == 'KP': it.key_states[str(pts[1])] = int(float(pts[2]))
    try:
        with open(args.file, 'r') as f: code = f.read()
        it.run_code(code)
    except Exception as e: print(f"INTERPRETER CRASH: {e}")
    out_img = it.front_buffer if it.front_buffer else it.images.get("main")
    if out_img: out_img.save(args.output); print(f"Saved to {args.output}")
    print("Done.")
