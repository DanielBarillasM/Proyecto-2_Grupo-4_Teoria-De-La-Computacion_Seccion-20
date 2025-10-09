from typing import Dict, List, Set, Tuple

class Grammar:
    """Representa una gramática libre de contexto (CFG)."""
    def __init__(self):
        self.productions: Dict[str, List[List[str]]] = {}
        self.non_terminals: Set[str] = set()
        self.terminals: Set[str] = set()
        self.start_symbol: str = 'S'

    def add_production(self, lhs: str, rhs: List[str]) -> bool:
        if not lhs or not isinstance(lhs, str):
            raise ValueError("El lado izquierdo debe ser una cadena no vacía")
        if not rhs or not isinstance(rhs, list):
            raise ValueError("El lado derecho debe ser una lista no vacía")
        if lhs not in self.productions:
            self.productions[lhs] = []
        self.productions[lhs].append(rhs)
        self.non_terminals.add(lhs)  # LHS siempre NT
        return True

    def recompute_symbol_sets(self) -> None:
        """Recalcula terminales vs no terminales."""
        self.terminals.clear()
        for rhs_list in self.productions.values():
            for rhs in rhs_list:
                for symbol in rhs:
                    if symbol not in self.non_terminals and symbol not in ('ε', 'e', ''):
                        self.terminals.add(symbol)

    def get_productions(self) -> Dict[str, List[List[str]]]:
        return self.productions.copy()

    def display_grammar(self) -> str:
        try:
            lines = []
            for lhs in sorted(self.productions.keys()):
                alts = " | ".join(" ".join(rhs) for rhs in self.productions[lhs])
                lines.append(f"{lhs} → {alts}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error al mostrar gramática: {e}"

    def to_text_format(self) -> str:
        lines = []
        for lhs in sorted(self.productions.keys()):
            for rhs in self.productions[lhs]:
                lines.append(f"{lhs} -> {' '.join(rhs)}")
        return "\n".join(lines)

    def validate(self) -> Tuple[bool, str]:
        if not self.productions:
            return False, "La gramática está vacía"
        if self.start_symbol not in self.productions:
            return False, f"Símbolo inicial '{self.start_symbol}' no encontrado"
        referenced_nt = set()
        for rhs_list in self.productions.values():
            for rhs in rhs_list:
                for symbol in rhs:
                    if symbol in self.non_terminals:
                        referenced_nt.add(symbol)
        undefined_nt = referenced_nt - set(self.productions.keys())
        if undefined_nt:
            return False, f"No terminales sin definir: {', '.join(sorted(undefined_nt))}"
        return True, "Gramática válida"