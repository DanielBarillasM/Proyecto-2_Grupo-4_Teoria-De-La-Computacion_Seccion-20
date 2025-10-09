from typing import Dict, List, Set, Tuple, Optional
from grammar import Grammar
from logger import LogFn, noop_logger

class CNFConverter:
    """Conversor a Forma Normal de Chomsky (sin dependencias de UI)."""
    def __init__(self, grammar: Grammar, log: LogFn = noop_logger):
        self.grammar = grammar
        self.new_var_counter = 0
        self.conversion_steps: List[str] = []
        self.original_S_was_nullable = False
        self.log = log

    def _log(self, level: str, msg: str) -> None:
        try:
            self.log(level, msg)
        except Exception:
            pass

    def get_new_variable(self) -> str:
        """Genera una nueva variable no terminal única (X0, X1, ...)."""
        while True:
            var = f"X{self.new_var_counter}"
            self.new_var_counter += 1
            if var not in self.grammar.non_terminals and var not in self.grammar.productions:
                self.grammar.non_terminals.add(var)
                return var

    def eliminate_epsilon(self) -> None:
        self._log("info", "**Paso 1: Eliminando producciones epsilon (ε)**")
        nullable: Set[str] = set()
        changed, iterations, max_iterations = True, 0, 100
        while changed and iterations < max_iterations:
            changed, iterations = False, iterations + 1
            for lhs, rhs_list in self.grammar.productions.items():
                if lhs in nullable:
                    continue
                for rhs in rhs_list:
                    if len(rhs) == 1 and rhs[0] in ('e', 'ε'):
                        nullable.add(lhs); changed = True
                        self._log("info", f"  • {lhs} puede derivar ε (producción directa)")
                    elif rhs and all(s in nullable for s in rhs):
                        nullable.add(lhs); changed = True
                        self._log("info", f"  • {lhs} puede derivar ε (todos los símbolos son nullable)")
        if self.grammar.start_symbol in nullable:
            self.original_S_was_nullable = True

        new_productions: Dict[str, List[List[str]]] = {}
        for lhs, rhs_list in self.grammar.productions.items():
            new_productions[lhs] = []
            for rhs in rhs_list:
                if len(rhs) == 1 and rhs[0] in ('e', 'ε'):
                    continue
                for combo in self._generate_combinations(rhs, nullable):
                    if combo and combo not in new_productions[lhs]:
                        new_productions[lhs].append(combo)

        self.grammar.productions = {k: v for k, v in new_productions.items() if v}
        self.conversion_steps.append("Eliminación de producciones epsilon completada")
        self._log("success", "Producciones epsilon eliminadas")

    def _generate_combinations(self, rhs: List[str], nullable: Set[str]) -> List[List[str]]:
        if not rhs:
            return [[]]
        first, *rest = rhs
        combos_rest = self._generate_combinations(rest, nullable)
        result: List[List[str]] = []
        for c in combos_rest:
            result.append([first] + c)
            if first in nullable and c not in result:
                result.append(c)
        return result

    def eliminate_unit_productions(self) -> None:
        self._log("info", "**Paso 2: Eliminando producciones unitarias**")
        unit_productions = set()
        for lhs, rhs_list in self.grammar.productions.items():
            for rhs in rhs_list:
                if len(rhs) == 1 and rhs[0] in self.grammar.non_terminals:
                    unit_productions.add((lhs, rhs[0]))
                    self._log("info", f"  • Encontrada producción unitaria: {lhs} → {rhs[0]}")

        if not unit_productions:
            self._log("info", "No se encontraron producciones unitarias")
            return

        unit_closure = set(unit_productions)
        changed, iterations, max_iterations = True, 0, 50
        while changed and iterations < max_iterations:
            changed, iterations = False, iterations + 1
            new_pairs = set()
            for a, b in unit_closure:
                for b2, c in unit_closure:
                    if b == b2 and (a, c) not in unit_closure:
                        new_pairs.add((a, c)); changed = True
            unit_closure.update(new_pairs)

        new_productions: Dict[str, List[List[str]]] = {}
        for lhs in self.grammar.non_terminals:
            new_productions[lhs] = []
            for rhs in self.grammar.productions.get(lhs, []):
                if not (len(rhs) == 1 and rhs[0] in self.grammar.non_terminals):
                    new_productions[lhs].append(rhs)
            for a, b in unit_closure:
                if a == lhs:
                    for rhs in self.grammar.productions.get(b, []):
                        if not (len(rhs) == 1 and rhs[0] in self.grammar.non_terminals):
                            if rhs not in new_productions[lhs]:
                                new_productions[lhs].append(rhs)

        self.grammar.productions = {k: v for k, v in new_productions.items() if v}
        self.conversion_steps.append("Eliminación de producciones unitarias completada")
        self._log("success", "Producciones unitarias eliminadas")

    def remove_useless_symbols(self) -> None:
        self._log("info", "**Paso 3: Eliminando símbolos inútiles**")

        # No generadores
        generating: Set[str] = set()
        changed, iterations = True, 0
        while changed and iterations < 50:
            changed, iterations = False, iterations + 1
            for lhs, rhs_list in self.grammar.productions.items():
                if lhs in generating:
                    continue
                for rhs in rhs_list:
                    if all((s in self.grammar.terminals) or (s in generating) for s in rhs):
                        generating.add(lhs); changed = True
                        self._log("info", f"  • {lhs} es generador")
                        break

        old_count = len(self.grammar.productions)
        self.grammar.productions = {
            lhs: [rhs for rhs in rhs_list if all((s in self.grammar.terminals) or (s in generating) for s in rhs)]
            for lhs, rhs_list in self.grammar.productions.items() if lhs in generating
        }
        self.grammar.productions = {k: v for k, v in self.grammar.productions.items() if v}
        removed_ng = old_count - len(self.grammar.productions)
        if removed_ng > 0:
            self._log("info", f"  • Eliminados {removed_ng} símbolos no generadores")

        # Inalcanzables
        reachable = {self.grammar.start_symbol}
        changed, iterations = True, 0
        while changed and iterations < 50:
            changed, iterations = False, iterations + 1
            for lhs in list(reachable):
                for rhs in self.grammar.productions.get(lhs, []):
                    for s in rhs:
                        if s in self.grammar.non_terminals and s not in reachable:
                            reachable.add(s); changed = True
                            self._log("info", f"  • {s} es alcanzable desde {lhs}")

        old_count = len(self.grammar.productions)
        self.grammar.productions = {lhs: rhs_list for lhs, rhs_list in self.grammar.productions.items() if lhs in reachable}
        removed_unreach = old_count - len(self.grammar.productions)
        if removed_unreach > 0:
            self._log("info", f"  • Eliminados {removed_unreach} símbolos inalcanzables")

        self.grammar.non_terminals = set(self.grammar.productions.keys())
        self.conversion_steps.append("Eliminación de símbolos inútiles completada")
        self._log("success", "Símbolos inútiles eliminados")

    def augment_start_if_nullable(self) -> None:
        if self.original_S_was_nullable:
            self._log("info", "**Paso 4: Aumentando gramática (S derivaba ε)**")
            S0 = "S0"
            while S0 in self.grammar.productions:
                S0 += "0"
            old_start = self.grammar.start_symbol
            self.grammar.productions[S0] = [[old_start], ['ε']]
            self.grammar.non_terminals.add(S0)
            self.grammar.start_symbol = S0
            self._log("info", f"  • Nuevo símbolo inicial: {S0} → {old_start} | ε")

    def convert_to_cnf(self) -> None:
        self._log("info", "**Paso 5: Convirtiendo a Forma Normal de Chomsky**")
        new_productions: Dict[str, List[List[str]]] = {}
        terminal_vars: Dict[str, str] = {}

        for lhs, rhs_list in self.grammar.productions.items():
            new_productions[lhs] = []
            for rhs in rhs_list:
                if len(rhs) == 1:
                    a = rhs[0]
                    if a in ('ε', 'e'):
                        if lhs == self.grammar.start_symbol:
                            new_productions[lhs].append([a])
                            self._log("info", f"  • {lhs} → {a} (epsilon en símbolo inicial - CNF válido)")
                        else:
                            self._log("info", f"  • Descartando {lhs} → {a} (epsilon fuera del símbolo inicial)")
                        continue
                    if a in self.grammar.terminals:
                        new_productions[lhs].append([a])
                        self._log("info", f"  • {lhs} → {a} (terminal, ya en CNF)")
                    else:
                        self._log("warning", f"  ⚠ Ignorando producción unitaria residual: {lhs} → {a}")
                        continue

                elif len(rhs) == 2:
                    new_rhs: List[str] = []
                    for s in rhs:
                        if s in self.grammar.terminals:
                            if s not in terminal_vars:
                                tv = self.get_new_variable()
                                terminal_vars[s] = tv
                                new_productions[tv] = [[s]]
                                self._log("info", f"  • Nueva variable: {tv} → {s}")
                            new_rhs.append(terminal_vars[s])
                        else:
                            new_rhs.append(s)
                    new_productions[lhs].append(new_rhs)
                    self._log("info", f"  • {lhs} → {' '.join(new_rhs)}")

                else:
                    new_rhs = self._convert_long_production(rhs, new_productions, terminal_vars)
                    new_productions[lhs].append(new_rhs)
                    self._log("info", f"  • {lhs} → {' '.join(new_rhs)} (dividido de {' '.join(rhs)})")

        self.grammar.productions = {k: v for k, v in new_productions.items() if v}
        self.grammar.non_terminals = set(self.grammar.productions.keys())
        self.conversion_steps.append("Conversión a CNF completada")
        self._log("success", "Gramática convertida a Forma Normal de Chomsky")

    def _convert_long_production(self, rhs: List[str], new_productions: Dict, terminal_vars: Dict[str, str]) -> List[str]:
        if len(rhs) <= 2:
            return rhs
        first = rhs[0]
        if first in self.grammar.terminals:
            if first not in terminal_vars:
                tv = self.get_new_variable()
                terminal_vars[first] = tv
                new_productions[tv] = [[first]]
            first = terminal_vars[first]
        new_var = self.get_new_variable()
        remaining = rhs[1:]
        if len(remaining) > 2:
            remaining = self._convert_long_production(remaining, new_productions, terminal_vars)
        else:
            for i, s in enumerate(remaining):
                if s in self.grammar.terminals:
                    if s not in terminal_vars:
                        tv = self.get_new_variable()
                        terminal_vars[s] = tv
                        new_productions[tv] = [[s]]
                    remaining[i] = terminal_vars[s]
        new_productions[new_var] = [remaining]
        return [first, new_var]

    def convert(self) -> Tuple[Grammar, bool]:
        self._log("info", "### Proceso de Conversión a Forma Normal de Chomsky")
        ok, msg = self.grammar.validate()
        if not ok:
            self._log("error", f"Gramática inválida: {msg}")
            return self.grammar, False

        self._log("code", self.grammar.display_grammar())
        self.eliminate_epsilon(); self.grammar.recompute_symbol_sets()
        self._log("code", self.grammar.display_grammar())

        self.eliminate_unit_productions(); self.grammar.recompute_symbol_sets()
        self._log("code", self.grammar.display_grammar())

        self.remove_useless_symbols(); self.grammar.recompute_symbol_sets()
        self._log("code", self.grammar.display_grammar())

        self.augment_start_if_nullable(); self.grammar.recompute_symbol_sets()
        if self.original_S_was_nullable:
            self._log("code", self.grammar.display_grammar())
            self._log("info", "**Re-eliminando producciones unitarias tras aumento de start:**")
            self.eliminate_unit_productions(); self.grammar.recompute_symbol_sets()
            self._log("code", self.grammar.display_grammar())

        self.convert_to_cnf(); self.grammar.recompute_symbol_sets()
        self._log("code", self.grammar.display_grammar())

        ok, msg = self.grammar.validate()
        if ok:
            self._log("success", "Conversión a CNF completada exitosamente")
        else:
            self._log("error", f"Error en conversión: {msg}")
        return self.grammar, ok