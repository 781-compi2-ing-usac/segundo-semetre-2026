class CompilerError(Exception):
    def __init__(self, message, node=None, lineno=None, phase="unknown"):
        self.message = message
        self.node = node
        self.lineno = lineno or (getattr(node, "lineno", None) if node else None)
        self.phase = phase
        self.node_type = type(node).__name__ if node else None
        self.trace = []
        super().__init__(self.format())

    def format(self):
        parts = [f"[{self.phase.upper()}]"]
        if self.lineno:
            parts.append(f"(line {self.lineno})")
        if self.node_type:
            parts.append(f"in {self.node_type}")
        parts.append(self.message)
        result = " ".join(parts)
        if self.trace:
            chain = " -> ".join(type(n).__name__ for n in self.trace)
            result += f"\n  Trace: {chain}"
        return result

    def to_dict(self):
        d = {
            "phase": self.phase,
            "message": self.message,
            "node_type": self.node_type,
        }
        if self.lineno:
            d["lineno"] = self.lineno
        if self.trace:
            d["trace"] = [type(n).__name__ for n in self.trace]
        return d


class ParseError(CompilerError):
    def __init__(self, message, lineno=None, **kwargs):
        super().__init__(message, lineno=lineno, phase="parse", **kwargs)


class TypeCheckError(CompilerError):
    def __init__(self, message, node=None, **kwargs):
        super().__init__(message, node=node, phase="typecheck", **kwargs)


class RuntimeError_(CompilerError):
    def __init__(self, message, node=None, **kwargs):
        super().__init__(message, node=node, phase="runtime", **kwargs)


class SymbolError(CompilerError):
    def __init__(self, message, name=None, **kwargs):
        self.symbol_name = name
        super().__init__(message, phase="symbol", **kwargs)
