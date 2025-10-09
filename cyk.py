import time
from typing import Dict, List, Set, Tuple, Optional
from grammar import Grammar
from logger import LogFn, noop_logger

class CYKParser:
    """Algoritmo CYK (backend puro, sin Streamlit)."""
    def __init__(self, grammar: Grammar, log: LogFn = noop_logger):
        self.grammar = grammar
        self.table: Optional[List[List[Set[str]]]] = None
        self.parse_table: Optional[List[List[Dict[str, list]]]] = None
        self.words: List[str] = []
        self.n: int = 0
        self.log = log
        self.binary_index = self._build_binary_index()
        self.terminal_index = self._build_terminal_index()

    def _log(self, level: str, msg: str) -> None:
        try: self.log(level, msg)
        except Exception: pass

    def _build_binary_index(self) -> Dict[Tuple[str, str], Set[str]]:
        idx: Dict[Tuple[str, str], Set[str]] = {}
        for lhs, rhs_list in self.grammar.productions.items():
            for rhs in rhs_list:
                if len(rhs) == 2:
                    idx.setdefault((rhs[0], rhs[1]), set()).add(lhs)
        return idx

    def _build_terminal_index(self) -> Dict[str, Set[str]]:
        idx: Dict[str, Set[str]] = {}
        for lhs, rhs_list in self.grammar.productions.items():
            for rhs in rhs_list:
                if len(rhs) == 1 and rhs[0] in self.grammar.terminals:
                    idx.setdefault(rhs[0], set()).add(lhs)
        return idx

    def parse(self, sentence: str) -> Tuple[bool, float, Optional[str], Dict]:
        start_time = time.time()
        sentence = (sentence or "").strip()
        self.words = [w.lower().strip() for w in sentence.split() if w.strip()]
        self.n = len(self.words)

        if self.n == 0:
            accepts_empty = any(len(rhs) == 1 and rhs[0] in ('ε', 'e')
                               for rhs in self.grammar.productions.get(self.grammar.start_symbol, []))
            parse_tree = f"{self.grammar.start_symbol} → ε\n" if accepts_empty else None
            return accepts_empty, time.time() - start_time, parse_tree, {
                "words": [], "length": 0, "table_filled_cells": 0, "total_cells": 0
            }

        self._log("info", f"**Analizando oración:** {' '.join(self.words)}")
        self._log("info", f"**Longitud:** {self.n} palabras")

        # Tokens desconocidos
        unknown = [w for w in self.words if w not in self.terminal_index]
        if unknown:
            msg = f"Palabras no reconocidas por la gramática: {', '.join(unknown)}"
            self._log("warning", f"⚠️ {msg}")
            return False, time.time() - start_time, None, {"error": msg, "unknown_words": unknown}

        # Tabla
        self.table = [[set() for _ in range(self.n)] for _ in range(self.n)]
        self.parse_table = [[{} for _ in range(self.n)] for _ in range(self.n)]

        # Diagonal
        self._log("info", "**Fase 1: Llenando diagonal principal**")
        for j in range(self.n):
            word = self.words[j]
            for lhs in self.terminal_index.get(word, []):
                self.table[j][j].add(lhs)
                self.parse_table[j][j].setdefault(lhs, []).append(('terminal', word))
                self._log("info", f"  • Posición [{j},{j}]: {lhs} → {word}")

        # Resto
        self._log("info", "**Fase 2: Llenando tabla con producciones no terminales**")
        for length in range(2, self.n + 1):
            for i in range(self.n - length + 1):
                j = i + length - 1
                for k in range(i, j):
                    left_cell = self.table[i][k]
                    right_cell = self.table[k+1][j]
                    if not left_cell or not right_cell:
                        continue
                    for B in left_cell:
                        for C in right_cell:
                            for lhs in self.binary_index.get((B, C), set()):
                                self.table[i][j].add(lhs)
                                self.parse_table[i][j].setdefault(lhs, []).append(('production', B, C, k))
                                self._log("info", f"  • Posición [{i},{j}]: {lhs} → {B} {C} (división en {k})")

        exec_time = time.time() - start_time
        accepted = self.grammar.start_symbol in self.table[0][self.n-1]
        parse_tree = self._build_parse_tree(self.grammar.start_symbol, 0, self.n-1) if accepted else None

        stats = {
            "words": self.words,
            "length": self.n,
            "table_filled_cells": sum(1 for i in range(self.n) for j in range(i, self.n) if self.table[i][j]),
            "total_cells": sum(range(1, self.n + 1))
        }
        return accepted, exec_time, parse_tree, stats

    def _build_parse_tree(self, symbol: str, i: int, j: int, indent: int = 0) -> str:
        prefix = "  " * indent
        if i == j:
            productions = self.parse_table[i][j].get(symbol, [])
            if productions:
                terminal = productions[0][1]
                return f"{prefix}{symbol} → {terminal}\n"
            return f"{prefix}{symbol} → ?\n"
        productions = self.parse_table[i][j].get(symbol, [])
        if productions:
            info = productions[0]
            if len(info) >= 4:
                _, B, C, k = info
                result = f"{prefix}{symbol} → {B} {C}\n"
                result += self._build_parse_tree(B, i, k, indent + 1)
                result += self._build_parse_tree(C, k + 1, j, indent + 1)
                return result
            return f"{prefix}{symbol} → ? (información incompleta)\n"
        return f"{prefix}{symbol} → ? (no encontrado)\n"