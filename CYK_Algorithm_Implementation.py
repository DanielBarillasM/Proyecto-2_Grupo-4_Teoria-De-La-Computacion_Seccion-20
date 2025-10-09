import streamlit as st
import time
from typing import Dict, List, Set, Tuple, Optional
import pandas as pd

class Grammar:
    """Clase para representar una gramática libre de contexto"""
    
    def __init__(self, start_symbol: Optional[str] = None):
        self.productions: Dict[str, List[List[str]]] = {}
        self.non_terminals: Set[str] = set()
        self.terminals: Set[str] = set()
        # Por defecto 'S' si no se especifica; el loader puede sobreescribirlo
        self.start_symbol = start_symbol or 'S'
    
    def add_production(self, lhs: str, rhs: List[str]):
        """Añade una producción a la gramática"""
        try:
            if not lhs or not isinstance(lhs, str):
                raise ValueError("El lado izquierdo debe ser una cadena no vacía")
            
            if not rhs or not isinstance(rhs, list):
                raise ValueError("El lado derecho debe ser una lista no vacía")
            
            if lhs not in self.productions:
                self.productions[lhs] = []
            
            self.productions[lhs].append(rhs)
            # LHS siempre es no terminal
            self.non_terminals.add(lhs)
                    
        except Exception as e:
            st.error(f"Error al añadir producción {lhs} → {' '.join(rhs)}: {str(e)}")
            return False
        return True
    
    def recompute_symbol_sets(self):
        """Recomputa los conjuntos de terminales y no terminales correctamente"""
        # Limpiar terminales previos
        self.terminals.clear()
        
        # Todo símbolo de RHS que no esté en non_terminals es terminal
        for rhs_list in self.productions.values():
            for rhs in rhs_list:
                for symbol in rhs:
                    if symbol not in self.non_terminals and symbol not in ('ε', 'e', ''):
                        self.terminals.add(symbol)
    
    def get_productions(self):
        """Obtiene todas las producciones"""
        return self.productions.copy()
    
    def display_grammar(self) -> str:
        """Muestra la gramática de forma legible"""
        try:
            result = []
            for lhs in sorted(self.productions.keys()):
                rhs_list = self.productions[lhs]
                productions = " | ".join([" ".join(rhs) for rhs in rhs_list])
                result.append(f"{lhs} → {productions}")
            return "\n".join(result)
        except Exception as e:
            return f"Error al mostrar gramática: {str(e)}"
    
    def to_text_format(self) -> str:
        """Convierte la gramática a formato texto para descarga"""
        result = []
        for lhs in sorted(self.productions.keys()):
            rhs_list = self.productions[lhs]
            for rhs in rhs_list:
                result.append(f"{lhs} -> {' '.join(rhs)}")
        return "\n".join(result)
    
    def validate(self) -> Tuple[bool, str]:
        try:
            if not self.productions:
                return False, "La gramática está vacía"

            if self.start_symbol not in self.productions:
                return False, f"Símbolo inicial '{self.start_symbol}' no encontrado"

            # Detectar NTs referenciados: o bien son LHS conocidos o con convención de mayúsculas
            referenced_nt = set()
            lhs_set = set(self.productions.keys())
            for rhs_list in self.productions.values():
                for rhs in rhs_list:
                    for symbol in rhs:
                        if symbol in ('ε', 'e', ''):
                            continue
                        # Heurística: si es LHS o parece NT (Empieza en mayúscula y no es solo puntuación)
                        if symbol in lhs_set or (symbol[:1].isupper() and any(ch.isalnum() for ch in symbol)):
                            referenced_nt.add(symbol)

            undefined_nt = {s for s in referenced_nt if s not in lhs_set}
            if undefined_nt:
                return False, f"No terminales sin definir: {', '.join(sorted(undefined_nt))}"

            return True, "Gramática válida"
        except Exception as e:
            return False, f"Error en validación: {str(e)}"

class CNFConverter:
    """Conversor a Forma Normal de Chomsky"""
    
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.new_var_counter = 0
        self.conversion_steps = []
        self.original_S_was_nullable = False
    
    def get_new_variable(self) -> str:
        """Genera una nueva variable no terminal única"""
        while True:
            var = f"X{self.new_var_counter}"
            self.new_var_counter += 1
            if var not in self.grammar.non_terminals and var not in self.grammar.productions:
                self.grammar.non_terminals.add(var)
                return var
    
    def eliminate_epsilon(self):
        """Paso 1: Elimina producciones epsilon (ε)"""
        try:
            st.write("**Paso 1: Eliminando producciones epsilon (ε)**")
            
            # Encontrar variables que pueden derivar epsilon
            nullable = set()
            changed = True
            iterations = 0
            max_iterations = 100
            
            while changed and iterations < max_iterations:
                changed = False
                iterations += 1
                
                for lhs, rhs_list in self.grammar.productions.items():
                    if lhs not in nullable:
                        for rhs in rhs_list:
                            # Producción epsilon explícita - NORMALIZADO
                            if len(rhs) == 1 and (rhs[0] == 'ε' or rhs[0] == 'e'):
                                nullable.add(lhs)
                                changed = True
                                st.write(f"  • {lhs} puede derivar ε (producción directa)")
                            # CORRECCIÓN: Todos los símbolos de RHS deben ser nullable
                            elif rhs and all(symbol in nullable for symbol in rhs):
                                nullable.add(lhs)
                                changed = True
                                st.write(f"  • {lhs} puede derivar ε (todos los símbolos son nullable)")
            
            # Recordar si S era nullable
            if self.grammar.start_symbol in nullable:
                self.original_S_was_nullable = True
            
            # Crear nuevas producciones sin epsilon
            new_productions = {}
            for lhs, rhs_list in self.grammar.productions.items():
                new_productions[lhs] = []
                
                for rhs in rhs_list:
                    # Saltar producciones epsilon explícitas
                    if len(rhs) == 1 and (rhs[0] == 'e' or rhs[0] == 'ε'):
                        continue
                    
                    # Generar todas las combinaciones eliminando símbolos nullable
                    combinations = self._generate_combinations(rhs, nullable)
                    for combo in combinations:
                        if combo and combo not in new_productions[lhs]:
                            new_productions[lhs].append(combo)
            
            # Filtrar producciones vacías
            self.grammar.productions = {k: v for k, v in new_productions.items() if v}
            
            self.conversion_steps.append("Eliminación de producciones epsilon completada")
            st.success("Producciones epsilon eliminadas")
            
        except Exception as e:
            st.error(f"Error eliminando producciones epsilon: {str(e)}")
            raise
    
    def _generate_combinations(self, rhs: List[str], nullable: Set[str]) -> List[List[str]]:
        """Genera todas las combinaciones posibles eliminando variables nullable"""
        if not rhs:
            return [[]]
        
        combinations = []
        first, *rest = rhs
        rest_combinations = self._generate_combinations(rest, nullable)
        
        for rest_combo in rest_combinations:
            # Incluir el primer símbolo
            combinations.append([first] + rest_combo)
            
            # Si el primer símbolo es nullable, también generar sin él
            if first in nullable:
                if rest_combo not in combinations:
                    combinations.append(rest_combo)
        
        return combinations
    
    def eliminate_unit_productions(self):
        """Paso 2: Elimina producciones unitarias (A → B)"""
        try:
            st.write("**Paso 2: Eliminando producciones unitarias**")
            
            # Encontrar producciones unitarias
            unit_productions = set()
            for lhs, rhs_list in self.grammar.productions.items():
                for rhs in rhs_list:
                    if len(rhs) == 1 and rhs[0] in self.grammar.non_terminals:
                        unit_productions.add((lhs, rhs[0]))
                        st.write(f"  • Encontrada producción unitaria: {lhs} → {rhs[0]}")
            
            if not unit_productions:
                st.info("No se encontraron producciones unitarias")
                return
            
            # Calcular clausura transitiva
            unit_closure = set(unit_productions)
            changed = True
            iterations = 0
            max_iterations = 50
            
            while changed and iterations < max_iterations:
                changed = False
                iterations += 1
                new_pairs = set()
                
                for a, b in unit_closure:
                    for b2, c in unit_closure:
                        if b == b2 and (a, c) not in unit_closure:
                            new_pairs.add((a, c))
                            changed = True
                
                unit_closure.update(new_pairs)
            
            # Crear nuevas producciones eliminando unitarias
            new_productions = {}
            for lhs in self.grammar.non_terminals:
                new_productions[lhs] = []
                
                # Añadir producciones no unitarias del símbolo actual
                for rhs in self.grammar.productions.get(lhs, []):
                    if not (len(rhs) == 1 and rhs[0] in self.grammar.non_terminals):
                        new_productions[lhs].append(rhs)
                
                # Añadir producciones derivadas de la clausura transitiva
                for a, b in unit_closure:
                    if a == lhs:
                        for rhs in self.grammar.productions.get(b, []):
                            if not (len(rhs) == 1 and rhs[0] in self.grammar.non_terminals):
                                if rhs not in new_productions[lhs]:
                                    new_productions[lhs].append(rhs)
            
            # Filtrar producciones vacías
            self.grammar.productions = {k: v for k, v in new_productions.items() if v}
            
            self.conversion_steps.append("Eliminación de producciones unitarias completada")
            st.success("Producciones unitarias eliminadas")
            
        except Exception as e:
            st.error(f"Error eliminando producciones unitarias: {str(e)}")
            raise
    
    def remove_useless_symbols(self):
        """Paso 3: Elimina símbolos inútiles (no generadores e inalcanzables)"""
        try:
            st.write("**Paso 3: Eliminando símbolos inútiles**")
            
            # 1) Encontrar símbolos generadores
            generating = set()
            changed = True
            iterations = 0
            
            while changed and iterations < 50:
                changed = False
                iterations += 1
                
                for lhs, rhs_list in self.grammar.productions.items():
                    if lhs not in generating:
                        for rhs in rhs_list:
                            # Una producción es generadora si todos sus símbolos son terminales o generadores
                            if all((s in self.grammar.terminals) or (s in generating) for s in rhs):
                                generating.add(lhs)
                                changed = True
                                st.write(f"  • {lhs} es generador")
                                break
            
            # Filtrar símbolos no generadores
            old_count = len(self.grammar.productions)
            self.grammar.productions = {
                lhs: [rhs for rhs in rhs_list 
                      if all((s in self.grammar.terminals) or (s in generating) for s in rhs)]
                for lhs, rhs_list in self.grammar.productions.items() 
                if lhs in generating
            }
            
            # Filtrar producciones vacías
            self.grammar.productions = {k: v for k, v in self.grammar.productions.items() if v}
            
            removed_ng = old_count - len(self.grammar.productions)
            if removed_ng > 0:
                st.write(f"  • Eliminados {removed_ng} símbolos no generadores")
            
            # 2) Encontrar símbolos alcanzables desde S
            reachable = {self.grammar.start_symbol}
            changed = True
            iterations = 0
            
            while changed and iterations < 50:
                changed = False
                iterations += 1
                
                for lhs in list(reachable):
                    for rhs in self.grammar.productions.get(lhs, []):
                        for symbol in rhs:
                            if symbol in self.grammar.non_terminals and symbol not in reachable:
                                reachable.add(symbol)
                                changed = True
                                st.write(f"  • {symbol} es alcanzable desde {lhs}")
            
            # Filtrar símbolos inalcanzables
            old_count = len(self.grammar.productions)
            self.grammar.productions = {
                lhs: rhs_list for lhs, rhs_list in self.grammar.productions.items() 
                if lhs in reachable
            }
            
            removed_unreach = old_count - len(self.grammar.productions)
            if removed_unreach > 0:
                st.write(f"  • Eliminados {removed_unreach} símbolos inalcanzables")
            
            # Actualizar conjuntos
            self.grammar.non_terminals = set(self.grammar.productions.keys())
            
            self.conversion_steps.append("Eliminación de símbolos inútiles completada")
            st.success("Símbolos inútiles eliminados")
            
        except Exception as e:
            st.error(f"Error eliminando símbolos inútiles: {str(e)}")
            raise
    
    def augment_start_if_nullable(self):
        """Paso 4: Aumenta la gramática si S derivaba epsilon"""
        if self.original_S_was_nullable:
            st.write("**Paso 4: Aumentando gramática (S derivaba ε)**")
            
            S0 = "S0"
            while S0 in self.grammar.productions:
                S0 += "0"
            
            old_start = self.grammar.start_symbol
            self.grammar.productions[S0] = [[old_start], ['ε']]
            self.grammar.non_terminals.add(S0)
            self.grammar.start_symbol = S0
            
            st.write(f"  • Nuevo símbolo inicial: {S0} → {old_start} | ε")
    
    def convert_to_cnf(self):
        """Paso 5: Convierte a Forma Normal de Chomsky"""
        try:
            st.write("**Paso 5: Convirtiendo a Forma Normal de Chomsky**")
            
            new_productions = {}
            terminal_vars = {}  # Cache para variables de terminales
            
            for lhs, rhs_list in self.grammar.productions.items():
                new_productions[lhs] = []
                
                for rhs in rhs_list:
                    if len(rhs) == 1:
                        a = rhs[0]
                        # CORRECCIÓN: Permitir ε solo en símbolo inicial
                        if a in ('ε', 'e'):
                            if lhs == self.grammar.start_symbol:
                                new_productions[lhs].append([a])
                                st.write(f"  • {lhs} → {a} (epsilon en símbolo inicial - CNF válido)")
                                continue
                            else:
                                # Descartar ε fuera del start
                                st.write(f"  • Descartando {lhs} → {a} (epsilon fuera del símbolo inicial)")
                                continue
                        
                        if a in self.grammar.terminals:
                            new_productions[lhs].append([a])
                            st.write(f"  • {lhs} → {a} (terminal, ya en CNF)")
                        else:
                            # Es un no terminal - unitaria residual
                            st.warning(f"  ⚠ Ignorando producción unitaria residual: {lhs} → {a}")
                            continue
                        
                    elif len(rhs) == 2:
                        # A → BC - verificar si hay terminales
                        new_rhs = []
                        for symbol in rhs:
                            if symbol in self.grammar.terminals:
                                # Reemplazar terminal con nueva variable
                                if symbol not in terminal_vars:
                                    terminal_vars[symbol] = self.get_new_variable()
                                    new_productions[terminal_vars[symbol]] = [[symbol]]
                                    st.write(f"  • Nueva variable: {terminal_vars[symbol]} → {symbol}")
                                new_rhs.append(terminal_vars[symbol])
                            else:
                                new_rhs.append(symbol)
                        
                        new_productions[lhs].append(new_rhs)
                        st.write(f"  • {lhs} → {' '.join(new_rhs)}")
                        
                    else:
                        # Más de dos símbolos - dividir recursivamente
                        new_rhs = self._convert_long_production(rhs, new_productions, terminal_vars)
                        new_productions[lhs].append(new_rhs)
                        st.write(f"  • {lhs} → {' '.join(new_rhs)} (dividido de {' '.join(rhs)})")
            
            # Filtrar producciones vacías - MEJORADO
            self.grammar.productions = {k: v for k, v in new_productions.items() if v}
            # Actualizar conjunto de no terminales para excluir LHS sin reglas
            self.grammar.non_terminals = set(self.grammar.productions.keys())
            
            self.conversion_steps.append("Conversión a CNF completada")
            st.success("Gramática convertida a Forma Normal de Chomsky")
            
        except Exception as e:
            st.error(f"Error convirtiendo a CNF: {str(e)}")
            raise
    
    def _convert_long_production(self, rhs: List[str], new_productions: Dict, terminal_vars: Dict) -> List[str]:
        """Convierte una producción larga (>2 símbolos) a CNF"""
        if len(rhs) <= 2:
            return rhs
        
        # Procesar primer símbolo
        first = rhs[0]
        if first in self.grammar.terminals:
            if first not in terminal_vars:
                terminal_vars[first] = self.get_new_variable()
                new_productions[terminal_vars[first]] = [[first]]
            first = terminal_vars[first]
        
        # Crear nueva variable para el resto
        new_var = self.get_new_variable()
        remaining = rhs[1:]
        
        if len(remaining) > 2:
            # Recursivamente convertir el resto
            remaining = self._convert_long_production(remaining, new_productions, terminal_vars)
        else:
            # Procesar los últimos símbolos
            for i, symbol in enumerate(remaining):
                if symbol in self.grammar.terminals:
                    if symbol not in terminal_vars:
                        terminal_vars[symbol] = self.get_new_variable()
                        new_productions[terminal_vars[symbol]] = [[symbol]]
                    remaining[i] = terminal_vars[symbol]
        
        new_productions[new_var] = [remaining]
        return [first, new_var]
    
    def convert(self) -> Tuple[Grammar, bool]:
        """Convierte la gramática a CNF y devuelve resultado"""
        try:
            st.write("### Proceso de Conversión a Forma Normal de Chomsky")
            
            # Validar gramática original
            is_valid, message = self.grammar.validate()
            if not is_valid:
                st.error(f"Gramática inválida: {message}")
                return self.grammar, False
            
            # Mostrar gramática original
            st.write("**Gramática Original:**")
            st.code(self.grammar.display_grammar())
            
            # Pipeline completo de conversión
            self.eliminate_epsilon()
            self.grammar.recompute_symbol_sets()
            st.code(self.grammar.display_grammar())
            
            self.eliminate_unit_productions()
            self.grammar.recompute_symbol_sets()
            st.code(self.grammar.display_grammar())
            
            self.remove_useless_symbols()
            self.grammar.recompute_symbol_sets()
            st.code(self.grammar.display_grammar())
            
            self.augment_start_if_nullable()
            self.grammar.recompute_symbol_sets()
            if self.original_S_was_nullable:
                st.code(self.grammar.display_grammar())
                
                # 🔧 ARREGLO: eliminar la unitaria S0→S que acabamos de introducir
                st.write("**Re-eliminando producciones unitarias tras aumento de start:**")
                self.eliminate_unit_productions()
                self.grammar.recompute_symbol_sets()
                st.code(self.grammar.display_grammar())
            
            self.convert_to_cnf()
            self.grammar.recompute_symbol_sets()
            st.code(self.grammar.display_grammar())
            
            # Validar resultado
            is_valid, message = self.grammar.validate()
            if is_valid:
                st.success("Conversión a CNF completada exitosamente")
            else:
                st.error(f"Error en conversión: {message}")
            
            return self.grammar, is_valid
            
        except Exception as e:
            st.error(f"Error general en conversión: {str(e)}")
            return self.grammar, False

class CYKParser:
    """Implementación del algoritmo CYK con optimizaciones"""
    
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.table = None
        self.parse_table = None
        self.words = []
        self.n = 0
        # MEJORA: Índices optimizados para CYK
        self.binary_index = self._build_binary_index()
        self.terminal_index = self._build_terminal_index()
    
    def _build_binary_index(self) -> Dict[Tuple[str, str], Set[str]]:
        """Construye índice inverso para producciones binarias A → BC"""
        idx = {}
        for lhs, rhs_list in self.grammar.productions.items():
            for rhs in rhs_list:
                if len(rhs) == 2:
                    key = (rhs[0], rhs[1])
                    idx.setdefault(key, set()).add(lhs)
        return idx
    
    def _build_terminal_index(self) -> Dict[str, Set[str]]:
        """Construye índice inverso para producciones terminales A → a"""
        idx = {}
        for lhs, rhs_list in self.grammar.productions.items():
            for rhs in rhs_list:
                if len(rhs) == 1 and rhs[0] in self.grammar.terminals:
                    terminal = rhs[0]
                    idx.setdefault(terminal, set()).add(lhs)
        return idx
    
    def parse(self, sentence: str) -> Tuple[bool, float, Optional[str], Dict]:
        """Ejecuta el algoritmo CYK"""
        try:
            start_time = time.time()
            
            # Validar entrada
            if not sentence or not sentence.strip():
                sentence = ""
            
            # Tokenizar
            self.words = [word.strip() for word in sentence.strip().split() if word.strip()]
            self.n = len(self.words)
            
            # CORRECCIÓN: Manejar entrada vacía correctamente
            if self.n == 0:
                # Verificar si la gramática acepta cadena vacía
                accepts_empty = any(len(rhs) == 1 and rhs[0] in ('ε', 'e')
                                  for rhs in self.grammar.productions.get(self.grammar.start_symbol, []))
                parse_tree = f"{self.grammar.start_symbol} → ε\n" if accepts_empty else None
                return accepts_empty, time.time() - start_time, parse_tree, {
                    "words": [], 
                    "length": 0,
                    "table_filled_cells": 0,
                    "total_cells": 0
                }
            
            st.write(f"**Analizando oración:** {' '.join(self.words)}")
            st.write(f"**Longitud:** {self.n} palabras")
            
            # Verificar que todas las palabras están en la gramática - OPTIMIZADO
            unknown_words = []
            for word in self.words:
                # Usar índice de terminales para lookup O(1)
                if word not in self.terminal_index:
                    unknown_words.append(word)
            
            if unknown_words:
                error_msg = f"Palabras no reconocidas por la gramática: {', '.join(unknown_words)}"
                st.warning(f"⚠️ {error_msg}")
                return False, time.time() - start_time, None, {"error": error_msg, "unknown_words": unknown_words}
            
            # Inicializar tablas CYK
            self.table = [[set() for _ in range(self.n)] for _ in range(self.n)]
            self.parse_table = [[{} for _ in range(self.n)] for _ in range(self.n)]
            
            # Fase 1: Llenar diagonal (producciones terminales) - OPTIMIZADA
            st.write("**Fase 1: Llenando diagonal principal**")
            for j in range(self.n):
                word = self.words[j]
                # Usar índice de terminales para eficiencia O(1)
                if word in self.terminal_index:
                    for lhs in self.terminal_index[word]:
                        self.table[j][j].add(lhs)
                        if lhs not in self.parse_table[j][j]:
                            self.parse_table[j][j][lhs] = []
                        self.parse_table[j][j][lhs].append(('terminal', word))
                        st.write(f"  • Posición [{j},{j}]: {lhs} → {word}")
            
            # Fase 2: Llenar resto de la tabla - OPTIMIZADA
            st.write("**Fase 2: Llenando tabla con producciones no terminales**")
            for length in range(2, self.n + 1):  # Longitud de subcadena
                for i in range(self.n - length + 1):  # Posición inicial
                    j = i + length - 1  # Posición final
                    
                    for k in range(i, j):  # Punto de división
                        left_cell = self.table[i][k]
                        right_cell = self.table[k+1][j]
                        
                        if not left_cell or not right_cell:
                            continue
                        
                        # OPTIMIZACIÓN: Usar índice binario para reducir factor |G|
                        for B in left_cell:
                            for C in right_cell:
                                key = (B, C)
                                if key in self.binary_index:
                                    for lhs in self.binary_index[key]:
                                        self.table[i][j].add(lhs)
                                        if lhs not in self.parse_table[i][j]:
                                            self.parse_table[i][j][lhs] = []
                                        self.parse_table[i][j][lhs].append(('production', B, C, k))
                                        st.write(f"  • Posición [{i},{j}]: {lhs} → {B} {C} (división en {k})")
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Verificar si la oración es aceptada
            accepted = self.grammar.start_symbol in self.table[0][self.n-1]
            
            parse_tree = None
            if accepted:
                parse_tree = self._build_parse_tree(self.grammar.start_symbol, 0, self.n-1)
            
            stats = {
                "words": self.words,
                "length": self.n,
                "table_filled_cells": sum(1 for i in range(self.n) for j in range(i, self.n) if self.table[i][j]),
                "total_cells": sum(range(1, self.n + 1))
            }
            
            return accepted, execution_time, parse_tree, stats
            
        except Exception as e:
            st.error(f"Error en análisis CYK: {str(e)}")
            return False, 0, None, {"error": str(e)}
    
    def _build_parse_tree(self, symbol: str, i: int, j: int, indent: int = 0) -> str:
        """Construye el árbol de análisis sintáctico recursivamente"""
        try:
            prefix = "  " * indent
            
            if i == j:  # Caso base: terminal
                productions = self.parse_table[i][j].get(symbol, [])
                if productions:
                    terminal = productions[0][1]
                    return f"{prefix}{symbol} → {terminal}\n"
                else:
                    return f"{prefix}{symbol} → ?\n"
            else:  # Caso recursivo: no terminal
                productions = self.parse_table[i][j].get(symbol, [])
                if productions:
                    prod_info = productions[0]  # Tomar primera producción
                    if len(prod_info) >= 4:
                        _, B, C, k = prod_info
                        result = f"{prefix}{symbol} → {B} {C}\n"
                        result += self._build_parse_tree(B, i, k, indent + 1)
                        result += self._build_parse_tree(C, k + 1, j, indent + 1)
                        return result
                    else:
                        return f"{prefix}{symbol} → ? (información incompleta)\n"
                else:
                    return f"{prefix}{symbol} → ? (no encontrado)\n"
        except Exception as e:
            return f"{'  ' * indent}{symbol} → ERROR: {str(e)}\n"
    
    def display_table(self):
        """Muestra la tabla CYK de forma visual"""
        try:
            st.write("### Tabla CYK")
            
            if not self.table or self.n == 0:
                st.warning("Tabla CYK no disponible o entrada vacía")
                return
            
            # Preparar datos para la tabla
            table_data = []
            headers = [f"w{i+1}={self.words[i]}" for i in range(self.n)]
            
            for i in range(self.n-1, -1, -1):  # Desde arriba hacia abajo
                row = []
                for j in range(self.n):
                    if j >= i:
                        cell_content = ", ".join(sorted(self.table[i][j])) if self.table[i][j] else "∅"
                        row.append(cell_content)
                    else:
                        row.append("")
                table_data.append(row)
            
            # Crear DataFrame con índices mejorados
            df = pd.DataFrame(table_data, 
                            columns=headers,
                            index=[f"Nivel {i+1}" for i in range(self.n)])  # Nivel 1 = fila superior
            
            st.dataframe(df, use_container_width=True)
            
            # Estadísticas de la tabla
            filled_cells = sum(1 for i in range(self.n) for j in range(i, self.n) if self.table[i][j])
            total_cells = sum(range(1, self.n + 1)) if self.n > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Celdas llenadas", filled_cells)
            with col2:
                st.metric("Total de celdas", total_cells)
            with col3:
                if total_cells > 0:
                    st.metric("Porcentaje lleno", f"{(filled_cells/total_cells)*100:.1f}%")
                else:
                    st.metric("Porcentaje lleno", "0%")
                
        except Exception as e:
            st.error(f"Error mostrando tabla CYK: {str(e)}")

def load_grammar_from_text(text: str) -> Grammar:
    """Carga una gramática desde texto formato A -> α | β (con autodetección de start)"""
    grammar = Grammar()
    try:
        lines = text.strip().split('\n')
        first_lhs: Optional[str] = None
        explicit_start: Optional[str] = None

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue

            # Directivas opcionales de inicio: "%start E" o "start: E"
            lower = line.lower()
            if lower.startswith('%start '):
                explicit_start = line.split(None, 1)[1].strip()
                continue
            if lower.startswith('start:'):
                explicit_start = line.split(':', 1)[1].strip()
                continue

            if '->' in line:
                parts = line.split('->', 1)
                lhs = parts[0].strip()
                rhs_text = parts[1].strip()

                if first_lhs is None:
                    first_lhs = lhs  # guardar primer LHS visto

                # Múltiples alternativas separadas por '|'
                rhs_alternatives = [alt.strip() for alt in rhs_text.split('|')] if '|' in rhs_text else [rhs_text]

                for rhs_alt in rhs_alternatives:
                    if rhs_alt:
                        rhs_symbols = rhs_alt.split()
                        # Normalizar epsilon
                        rhs_symbols = ['ε' if s in ('e', 'epsilon') else s for s in rhs_symbols]
                        grammar.add_production(lhs, rhs_symbols)

        grammar.recompute_symbol_sets()

        # Establecer símbolo inicial por prioridad: explícito > primer LHS > (dejar el que esté)
        if explicit_start:
            grammar.start_symbol = explicit_start
        elif grammar.start_symbol not in grammar.productions and first_lhs:
            grammar.start_symbol = first_lhs

        return grammar
    except Exception as e:
        st.error(f"Error cargando gramática: {str(e)}")
        return Grammar()

def create_project_grammar() -> Grammar:
    """Crea la gramática exacta del proyecto según el PDF"""
    try:
        grammar = Grammar()
        
        # Producciones según el proyecto - CORRECCIÓN: gramática exacta del PDF
        grammar.add_production('S', ['NP', 'VP'])
        
        grammar.add_production('VP', ['VP', 'PP'])
        grammar.add_production('VP', ['V', 'NP'])
        grammar.add_production('VP', ['cooks'])
        grammar.add_production('VP', ['drinks'])
        grammar.add_production('VP', ['eats'])
        grammar.add_production('VP', ['cuts'])
        
        grammar.add_production('PP', ['P', 'NP'])
        
        grammar.add_production('NP', ['Det', 'N'])
        grammar.add_production('NP', ['he'])
        grammar.add_production('NP', ['she'])
        
        grammar.add_production('V', ['cooks'])
        grammar.add_production('V', ['drinks'])
        grammar.add_production('V', ['eats'])
        grammar.add_production('V', ['cuts'])
        
        grammar.add_production('P', ['in'])
        grammar.add_production('P', ['with'])
        
        grammar.add_production('N', ['cat'])
        grammar.add_production('N', ['dog'])
        grammar.add_production('N', ['beer'])
        grammar.add_production('N', ['cake'])
        grammar.add_production('N', ['juice'])
        grammar.add_production('N', ['meat'])
        grammar.add_production('N', ['soup'])
        grammar.add_production('N', ['fork'])
        grammar.add_production('N', ['knife'])
        grammar.add_production('N', ['oven'])
        grammar.add_production('N', ['spoon'])
        
        grammar.add_production('Det', ['a'])
        grammar.add_production('Det', ['the'])
        
        # CORRECCIÓN: Recomputar conjuntos después de cargar todas las producciones
        grammar.recompute_symbol_sets()
        
        return grammar
        
    except Exception as e:
        st.error(f"Error creando gramática del proyecto: {str(e)}")
        return Grammar()

def create_arithmetic_grammar() -> Grammar:
    """Crea gramática aritmética básica (equivalente a 1.txt)"""
    grammar = Grammar()
    
    # CORRECCIÓN: Establecer símbolo inicial para gramática aritmética
    grammar.start_symbol = 'E'
    
    # Expresiones aritméticas básicas
    grammar.add_production('E', ['E', '+', 'T'])
    grammar.add_production('E', ['T'])
    
    grammar.add_production('T', ['T', '*', 'F'])
    grammar.add_production('T', ['F'])
    
    grammar.add_production('F', ['(', 'E', ')'])
    grammar.add_production('F', ['id'])
    
    grammar.recompute_symbol_sets()
    return grammar

def generate_dot_tree(parse_tree: str, sentence: str) -> str:
    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    try:
        lines = parse_tree.strip().split('\n')
        # Nuevo: recolectar todos los LHS que aparecen en el árbol
        lhs_seen = set()
        for ln in lines:
            ct = ln.strip()
            if '→' in ct:
                lhs_seen.add(ct.split('→', 1)[0].strip())

        dot_lines = [
            'digraph ParseTree {',
            '    rankdir=TB;',
            '    node [shape=box, style=rounded];',
            '    edge [dir=none];'
        ]

        node_counter = 0
        node_stack = []

        for line in lines:
            level = len(line) - len(line.lstrip())
            content = line.strip()
            if '→' not in content:
                continue

            lhs, rhs = [p.strip() for p in content.split('→', 1)]
            node_id = f"n{node_counter}"; node_counter += 1

            while len(node_stack) > level // 2:
                node_stack.pop()

            dot_lines.append(f'    {node_id} [label="{_esc(lhs)}", fillcolor=lightblue, style="rounded,filled"];')
            if node_stack:
                dot_lines.append(f'    {node_stack[-1]} -> {node_id};')
            node_stack.append(node_id)

            rhs_tokens = rhs.split()
            # Nuevo criterio: hoja si es 1 token y ese token no aparece como LHS en el árbol
            is_terminal = (len(rhs_tokens) == 1 and rhs_tokens[0] not in lhs_seen)
            if is_terminal and rhs not in ('?', ''):
                leaf_id = f"n{node_counter}"; node_counter += 1
                dot_lines.append(f'    {leaf_id} [label="{_esc(rhs)}", shape=ellipse, fillcolor=lightgreen, style="filled"];')
                dot_lines.append(f'    {node_id} -> {leaf_id};')

        dot_lines.append('}')
        return '\n'.join(dot_lines)

    except Exception as e:
        return f'''digraph ParseTree {{
    node [shape=box];
    error [label="{_esc(f'Error generando árbol: {str(e)}')}", fillcolor=red, style=filled];
}}'''

def run_test_cases(parser: CYKParser):
    """Ejecuta casos de prueba predefinidos según el vocabulario detectado."""
    st.write("### Casos de Prueba Automatizados")

    # Detectar tipo de gramática por vocabulario (no por símbolo inicial)
    terms = set(parser.grammar.terminals)

    is_arith = {"id", "+", "*", "(", ")"}.issubset(terms)
    is_proj = {
        "he", "she", "the", "a",
        "cat", "dog", "beer", "cake", "juice", "meat", "soup",
        "fork", "knife", "oven", "spoon",
        "cooks", "drinks", "eats", "cuts",
        "with", "in"
    }.issubset(terms)

    if is_proj:
        grammar_type = "project"
        # Casos de prueba para gramática del proyecto
        test_cases = [
            # Casos válidos (requieren Det para NP excepto pronombres)
            ("she eats a cake with a fork", True, "Ejemplo del PDF"),
            ("the cat drinks the beer", True, "Ejemplo del PDF"),
            ("he cuts the meat with a knife", True, "Estructura similar"),
            ("a dog eats the soup", True, "NP requiere Det + N"),
            ("she drinks the juice in the oven", True, "VP -> VP PP"),
            ("the cat cooks", True, "VP -> verbo solo"),
            ("he drinks the beer with the fork", True, "VP -> VP PP complejo"),

            # Casos inválidos
            ("she eat cake", False, "Concordancia + sin Det"),
            ("the drinks beer", False, "Sin sujeto válido"),
            ("cat the eats", False, "Orden incorrecto"),
            ("with fork eats she", False, "Orden incorrecto"),
            ("she", False, "Oración incompleta"),
            ("", False, "Cadena vacía"),
            ("dog eats soup", False, "Sin determinantes requeridos"),
            ("she cuts meat", False, "Falta Det en 'meat'"),
            ("beautiful cat eats", False, "'beautiful' no está en gramática"),
        ]

    elif is_arith:
        grammar_type = "arithmetic"
        # Casos de prueba para gramática aritmética
        test_cases = [
            # Casos válidos
            ("id", True, "Factor simple"),
            ("id + id", True, "Suma simple"),
            ("id * id", True, "Multiplicación simple"),
            ("( id )", True, "Factor con paréntesis"),
            ("id + id * id", True, "Precedencia de operadores"),
            ("( id + id ) * id", True, "Paréntesis modifican precedencia"),
            ("id * ( id + id )", True, "Paréntesis anidados"),

            # Casos inválidos
            ("", False, "Cadena vacía"),
            ("+", False, "Solo operador"),
            ("id +", False, "Expresión incompleta"),
            ("+ id", False, "Operador sin operando izquierdo"),
            ("id + + id", False, "Operadores consecutivos"),
            ("( id", False, "Paréntesis no cerrado"),
            ("id )", False, "Paréntesis no abierto"),
            ("id id", False, "Dos identificadores consecutivos"),
            ("* id", False, "Multiplicación sin operando izquierdo"),
        ]

    else:
        st.info("No hay batería de tests predefinida para la gramática actual. "
                "Usa el tab de Análisis Individual o define tus propios casos.")
        return

    # Ejecutar pruebas
    results = []
    for sentence, expected, description in test_cases:
        try:
            accepted, exec_time, _, stats = parser.parse(sentence)
            status = "✅ PASS" if accepted == expected else "❌ FAIL"
            results.append({
                "Entrada": sentence if sentence else "(vacía)",
                "Esperado": "SÍ" if expected else "NO",
                "Obtenido": "SÍ" if accepted else "NO",
                "Estado": status,
                "Tiempo (ms)": f"{exec_time*1000:.2f}",
                "Descripción": description
            })
        except Exception as e:
            results.append({
                "Entrada": sentence if sentence else "(vacía)",
                "Esperado": "SÍ" if expected else "NO",
                "Obtenido": f"ERROR: {str(e)}",
                "Estado": "❌ ERROR",
                "Tiempo (ms)": "N/A",
                "Descripción": description
            })

    # Mostrar resultados
    df_results = pd.DataFrame(results)
    st.dataframe(df_results, use_container_width=True)

    # Estadísticas
    passed = sum(1 for r in results if "PASS" in r["Estado"])
    total = len(results)
    st.metric("Tests Pasados", f"{passed}/{total} ({(passed/total)*100:.1f}%)")

    # Mostrar tipo de gramática detectada
    grammar_name = "Gramática del Proyecto" if grammar_type == "project" else "Gramática Aritmética"
    st.info(f"📝 Tests ejecutados para: **{grammar_name}**")

def verify_cnf_format(grammar: Grammar) -> Tuple[bool, str]:
    """Verifica correctamente si una gramática está en CNF"""
    try:
        for lhs, rhs_list in grammar.productions.items():
            for rhs in rhs_list:
                if len(rhs) == 1:
                    a = rhs[0]
                    # CORRECCIÓN: Permitir ε solo en símbolo inicial
                    if a in ('ε', 'e'):
                        if lhs == grammar.start_symbol:
                            continue  # S → ε es válido en CNF
                        else:
                            return False, f"Epsilon fuera del símbolo inicial: {lhs} → ε"
                    # A -> a (debe ser terminal)
                    if a not in grammar.terminals:
                        return False, f"Producción unitaria residual: {lhs} → {a}"
                elif len(rhs) == 2:
                    # A -> BC (ambos deben ser no terminales)
                    if rhs[0] in grammar.terminals or rhs[1] in grammar.terminals:
                        return False, f"Producción binaria con terminales: {lhs} → {' '.join(rhs)}"
                else:
                    return False, f"Producción de longitud > 2: {lhs} → {' '.join(rhs)}"
        
        return True, "Gramática en CNF válida"
    except Exception as e:
        return False, f"Error verificando CNF: {str(e)}"

def main():
    """Función principal de la aplicación"""
    st.set_page_config(
        page_title="Algoritmo CYK - Teoría de la Computación",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("CFG → CNF → CYK — Analizador y Visualizador")
    st.markdown("**Teoría de la Computación 2025 - Proyecto 2**")
    st.markdown("*Algoritmo Cocke-Younger-Kasami para parsing de gramáticas CFG*")
    
    # Información del proyecto
    with st.expander("📋 Información del Proyecto", expanded=False):
        st.markdown("""
        ### Objetivos Completados:
        - ✅ **Simplificador completo**: ε-producciones, unitarias, símbolos inútiles, CNF
        - ✅ **Algoritmo CYK**: tabla triangular, backpointers, reconstrucción de parse tree  
        - ✅ **Salidas requeridas**: SÍ/NO + tiempo de ejecución + árbol sintáctico
        - ✅ **Documentación y pruebas**: casos de prueba automatizados
        """)
    
    try:
        # Selector de gramática
        st.write("## 📝 Selección de Gramática")
        
        grammar_option = st.radio(
            "Elige la gramática a usar:",
            ["Gramática del Proyecto (PDF)", "Gramática Aritmética", "Cargar desde Texto"],
            index=0
        )
        
        if grammar_option == "Gramática del Proyecto (PDF)":
            original_grammar = create_project_grammar()
            grammar_source = "Gramática del proyecto según PDF"
            
        elif grammar_option == "Gramática Aritmética": 
            original_grammar = create_arithmetic_grammar()
            grammar_source = "Gramática de expresiones aritméticas (E, T, F)"
            
        else:  # Cargar desde texto
            st.write("### Cargar Gramática desde Texto")
            st.write("Formato: `A -> α | β` (una producción por línea)")
            
            default_text = """S -> NP VP
VP -> VP PP | V NP | cooks | drinks | eats
PP -> P NP  
NP -> Det N | he | she
V -> cooks | drinks | eats
P -> in | with
N -> cat | beer | cake | fork
Det -> a | the"""
            
            grammar_text = st.text_area(
                "Producciones de la gramática:",
                value=default_text,
                height=200,
                help="Una producción por línea. Use | para alternativas."
            )
            
            if grammar_text.strip():
                original_grammar = load_grammar_from_text(grammar_text)
                grammar_source = "Gramática cargada desde texto"

                # 🔰 NUEVO: línea informativa del símbolo inicial detectado
                st.info(f"🔰 Símbolo inicial detectado: **{original_grammar.start_symbol}**")

            else:
                st.warning("Ingrese una gramática válida")
                return
        
        # Validar gramática
        is_valid, validation_msg = original_grammar.validate()
        if not is_valid:
            st.error(f"❌ Error en gramática: {validation_msg}")
            return
        
        st.success(f"✅ {validation_msg}")
        
        with st.expander("Ver Gramática Original"):
            st.code(original_grammar.display_grammar())
        
        # Convertir a CNF
        st.write("## 🔄 Conversión a Forma Normal de Chomsky")
        converter = CNFConverter(original_grammar)
        cnf_grammar, conversion_success = converter.convert()
        
        if not conversion_success:
            st.error("❌ Error en la conversión a CNF. No se puede continuar.")
            return
        
        # Verificar que efectivamente esté en CNF
        is_cnf, cnf_msg = verify_cnf_format(cnf_grammar)
        if is_cnf:
            st.success(f"✅ {cnf_msg}")
        else:
            st.error(f"❌ {cnf_msg}")
            return
        
        # Botón para descargar CNF
        col1, col2 = st.columns(2)
        with col1:
            cnf_text = cnf_grammar.to_text_format()
            st.download_button(
                "⬇️ Descargar CNF como .txt",
                cnf_text,
                file_name="grammar_cnf.txt",
                mime="text/plain"
            )
        
        with col2:
            st.metric("Producciones CNF", sum(len(rhs_list) for rhs_list in cnf_grammar.productions.values()))
        
        # Crear parser CYK
        parser = CYKParser(cnf_grammar)
        
        # Interfaz principal con tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Análisis Individual", "🧪 Casos de Prueba", "📊 Estadísticas", "📚 Documentación"])
        
        with tab1:
            st.write("### Analizador CYK")
            
            # Ejemplos específicos según la gramática seleccionada
            if grammar_option == "Gramática del Proyecto (PDF)":
                st.write("#### Ejemplos para Gramática del Proyecto:")
                example_col1, example_col2 = st.columns(2)
                
                with example_col1:
                    st.write("**✅ Oraciones Válidas:**")
                    valid_examples = [
                        "she eats a cake with a fork",
                        "the cat drinks the beer", 
                        "he cuts the meat with a knife",
                        "a dog eats the soup",
                        "she drinks the juice in the oven"
                    ]
                    for ex in valid_examples:
                        st.write(f"• {ex}")
                
                with example_col2:
                    st.write("**❌ Oraciones Inválidas:**")
                    invalid_examples = [
                        "she eat cake",  # Sin Det, concordancia
                        "dog eats soup",  # Sin Det requeridos  
                        "cat the eats",  # Orden incorrecto
                        "beautiful cat eats",  # 'beautiful' no está
                        "she cuts meat"  # Falta Det en 'meat'
                    ]
                    for ex in invalid_examples:
                        st.write(f"• {ex}")
            
            elif grammar_option == "Gramática Aritmética":
                st.write("#### Ejemplos para Gramática Aritmética:")
                example_col1, example_col2 = st.columns(2)
                
                with example_col1:
                    st.write("**✅ Expresiones Válidas:**")
                    valid_examples = [
                        "id + id * id",
                        "( id )",
                        "id * ( id + id )",
                        "( id + id ) * id"
                    ]
                    for ex in valid_examples:
                        st.write(f"• {ex}")
                
                with example_col2:
                    st.write("**❌ Expresiones Inválidas:**")
                    invalid_examples = [
                        "id *",  # Incompleta
                        "+ id id",  # Operador sin operando izq
                        "id + + id",  # Operadores consecutivos
                        "( id"  # Paréntesis no cerrado
                    ]
                    for ex in invalid_examples:
                        st.write(f"• {ex}")
            
            # Input del usuario - SOLUCIÓN CORREGIDA
            st.write("### Ingrese una oración/expresión para analizar:")
            
            default_sentence = "she eats a cake with a fork" if grammar_option == "Gramática del Proyecto (PDF)" else "id + id * id"
            
            # Inicializar valores por defecto en session_state ANTES de crear widgets
            if "sentence_input" not in st.session_state:
                st.session_state.sentence_input = default_sentence
            if "last_grammar_option" not in st.session_state:
                st.session_state.last_grammar_option = grammar_option
            
            # Reset cuando cambie la gramática
            if st.session_state.last_grammar_option != grammar_option:
                st.session_state.sentence_input = default_sentence
                st.session_state.last_grammar_option = grammar_option
            
            # Widget principal - usar key diferente
            sentence = st.text_input(
                "Texto a analizar:",
                key="sentence_input",
                placeholder="Escriba usando las palabras de la gramática seleccionada...",
                help=f"Use solo símbolos definidos en la {grammar_source.lower()}"
            )
            
            # Botones de ejemplo rápido - SOLUCIÓN: usar callback functions
            if grammar_option == "Gramática del Proyecto (PDF)":
                st.write("**Ejemplos rápidos:**")
                col1, col2, col3, col4 = st.columns(4)
                
                def set_example_1():
                    st.session_state.sentence_input = "she eats a cake with a fork"
                
                def set_example_2():
                    st.session_state.sentence_input = "the cat drinks the beer"
                
                def set_example_3():
                    st.session_state.sentence_input = "he cuts the meat with a knife"
                
                def set_example_4():
                    st.session_state.sentence_input = "dog eats soup"
                
                with col1:
                    st.button("Ejemplo 1", help="she eats a cake with a fork", on_click=set_example_1)
                with col2:
                    st.button("Ejemplo 2", help="the cat drinks the beer", on_click=set_example_2)
                with col3:
                    st.button("VP -> VP PP", help="he cuts the meat with a knife", on_click=set_example_3)
                with col4:
                    st.button("Oración inválida", help="dog eats soup", on_click=set_example_4)
            
            elif grammar_option == "Gramática Aritmética":
                st.write("**Ejemplos rápidos:**")
                col1, col2, col3, col4 = st.columns(4)
                
                def set_arith_example_1():
                    st.session_state.sentence_input = "id + id * id"
                
                def set_arith_example_2():
                    st.session_state.sentence_input = "( id + id ) * id"
                
                def set_arith_example_3():
                    st.session_state.sentence_input = "id * ( id + id )"
                
                def set_arith_example_4():
                    st.session_state.sentence_input = "+ id id"
                
                with col1:
                    st.button("Precedencia", help="id + id * id", on_click=set_arith_example_1)
                with col2:
                    st.button("Paréntesis", help="( id + id ) * id", on_click=set_arith_example_2)
                with col3:
                    st.button("Anidado", help="id * ( id + id )", on_click=set_arith_example_3)
                with col4:
                    st.button("Expresión inválida", help="+ id id", on_click=set_arith_example_4)
            
            # Análisis principal
            if st.button("🚀 Analizar con CYK", type="primary", use_container_width=True):
                if sentence and sentence.strip():
                    with st.spinner("Ejecutando algoritmo CYK..."):
                        accepted, exec_time, parse_tree, stats = parser.parse(sentence)
                        
                        # Resultados principales
                        result_col1, result_col2, result_col3 = st.columns(3)
                        
                        with result_col1:
                            if accepted:
                                st.success("✅ **SÍ** - Aceptada por la gramática")
                            else:
                                st.error("❌ **NO** - Rechazada por la gramática")
                        
                        with result_col2:
                            st.info(f"⏱️ **Tiempo CYK:** {exec_time:.6f} seg")
                        
                        with result_col3:
                            if 'error' not in stats:
                                st.metric("📏 Longitud", f"{stats['length']} tokens")
                        
                        # Manejo de errores
                        if 'error' in stats:
                            st.error(f"❌ **Error:** {stats['error']}")
                            if 'unknown_words' in stats:
                                st.write("**Tokens no reconocidos:**", ', '.join(stats['unknown_words']))
                                
                                # Mostrar vocabulario válido
                                st.write("**Vocabulario disponible:**")
                                valid_tokens = set()
                                for rhs_list in cnf_grammar.productions.values():
                                    for rhs in rhs_list:
                                        if len(rhs) == 1 and rhs[0] in cnf_grammar.terminals:
                                            valid_tokens.add(rhs[0])
                                st.write(", ".join(sorted(valid_tokens)))
                        else:
                            # Mostrar tabla CYK
                            parser.display_table()
                        
                        # Parse tree si existe
                        if parse_tree:
                            st.write("### 🌳 Árbol de Análisis Sintáctico")
                            st.code(parse_tree, language="")
                            
                            # Generar y ofrecer descarga de DOT - CORREGIDO
                            dot_code = generate_dot_tree(parse_tree, sentence)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    "⬇️ Descargar Parse Tree (.dot)",
                                    dot_code,
                                    file_name="parse_tree.dot",
                                    mime="text/plain",
                                    help="Para visualizar: dot -Tpng parse_tree.dot -o tree.png"
                                )
                            with col2:
                                st.download_button(
                                    "⬇️ Descargar Parse Tree (.txt)",
                                    parse_tree,
                                    file_name="parse_tree.txt",
                                    mime="text/plain"
                                )
                            
                            # Información adicional del parse tree
                            with st.expander("🔍 Análisis del Parse Tree"):
                                tree_lines = [line for line in parse_tree.strip().split('\n') if '→' in line]
                                st.write(f"**Nodos en el árbol:** {len(tree_lines)}")
                                st.write(f"**Profundidad máxima:** {max((len(line) - len(line.lstrip())) // 2 for line in tree_lines) + 1}")
                                
                                # MEJORA: Contar tipos de nodos con mayor precisión
                                def is_terminal_line(line: str) -> bool:
                                    rhs = line.split('→', 1)[1].strip().split()
                                    return len(rhs) == 1 and (rhs[0] in cnf_grammar.terminals or rhs[0] in {'ε', 'e'})
                                
                                terminals = sum(is_terminal_line(line) for line in tree_lines)
                                non_terminals = len(tree_lines) - terminals
                                st.write(f"**Nodos terminales:** {terminals}")
                                st.write(f"**Nodos no terminales:** {non_terminals}")
                        
                        # Mensaje final
                        if not ('error' in stats):
                            if accepted:
                                st.success("🎉 **¡Análisis exitoso!** La entrada es sintácticamente correcta.")
                            else:
                                st.info("ℹ️ La entrada no puede ser generada por esta gramática.")
                else:
                    st.warning("⚠️ Por favor ingrese texto para analizar.")
        
        with tab2:
            st.write("### 🧪 Ejecución de Casos de Prueba")
            st.write("Valida automáticamente el funcionamiento del algoritmo con múltiples casos.")

            # Crear gramática con epsilon para test
            st.write("#### Test Especial: Gramática que acepta cadena vacía")
            epsilon_grammar = Grammar()
            epsilon_grammar.add_production('S', ['A'])
            epsilon_grammar.add_production('A', ['a'])
            epsilon_grammar.add_production('A', ['ε'])
            epsilon_grammar.recompute_symbol_sets()

            epsilon_converter = CNFConverter(epsilon_grammar)
            epsilon_cnf, _ = epsilon_converter.convert()
            epsilon_parser = CYKParser(epsilon_cnf)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🧪 Test cadena vacía", help="Prueba con gramática que acepta ε"):
                    accepted, exec_time, parse_tree, stats = epsilon_parser.parse("")
                    if accepted:
                        st.success(f"✅ Cadena vacía ACEPTADA en {exec_time:.6f}s")
                        if parse_tree:
                            st.code(parse_tree)
                    else:
                        st.error("❌ Cadena vacía RECHAZADA")

            with col2:
                if st.button("🧪 Test 'a' con epsilon", help="Prueba 'a' con gramática que acepta ε"):
                    accepted, exec_time, parse_tree, stats = epsilon_parser.parse("a")
                    if accepted:
                        st.success(f"✅ 'a' ACEPTADA en {exec_time:.6f}s")
                    else:
                        st.error("❌ 'a' RECHAZADA")

            with st.expander("Ver gramática epsilon en CNF"):
                st.code(epsilon_cnf.display_grammar())

            if st.button("▶️ Ejecutar Todos los Tests", type="secondary"):
                with st.spinner("Ejecutando batería de pruebas..."):
                    run_test_cases(parser)
        
        with tab3:
            st.write("### 📊 Análisis de la Gramática y Estadísticas")
            
            # Estadísticas principales
            stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
            
            with stats_col1:
                st.metric("No Terminales", len(cnf_grammar.non_terminals))
                st.metric("Terminales", len(cnf_grammar.terminals))
            
            with stats_col2:
                total_productions = sum(len(rhs_list) for rhs_list in cnf_grammar.productions.values())
                st.metric("Producciones", total_productions)
                
                terminal_prods = sum(1 for rhs_list in cnf_grammar.productions.values() 
                                   for rhs in rhs_list if len(rhs) == 1)
                st.metric("Terminales (A→a)", terminal_prods)
            
            with stats_col3:
                binary_prods = sum(1 for rhs_list in cnf_grammar.productions.values() 
                                 for rhs in rhs_list if len(rhs) == 2)
                st.metric("Binarias (A→BC)", binary_prods)
                
                st.metric("Forma CNF", "✅" if is_cnf else "❌")
            
            with stats_col4:
                st.write("**Complejidad CYK:**")
                st.write("• Tiempo: O(n³|G|)")
                st.write("• Espacio: O(n²)")
                st.write("• n = longitud entrada")
                st.write("• |G| = tamaño gramática")
            
            # Detalles de producciones CNF
            with st.expander("🔍 Análisis Detallado de Producciones CNF"):
                terminal_prods = []
                binary_prods = []
                
                for lhs, rhs_list in cnf_grammar.productions.items():
                    for rhs in rhs_list:
                        if len(rhs) == 1:
                            terminal_prods.append(f"{lhs} → {rhs[0]}")
                        elif len(rhs) == 2:
                            binary_prods.append(f"{lhs} → {rhs[0]} {rhs[1]}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Producciones A → a ({len(terminal_prods)}):**")
                    for prod in sorted(terminal_prods):
                        st.write(f"• {prod}")
                
                with col2:
                    st.write(f"**Producciones A → BC ({len(binary_prods)}):**")
                    for prod in sorted(binary_prods):
                        st.write(f"• {prod}")
            
            # Comparación con gramática original
            with st.expander("📈 Comparación: Original vs CNF"):
                orig_total = sum(len(rhs_list) for rhs_list in original_grammar.productions.values())
                cnf_total = sum(len(rhs_list) for rhs_list in cnf_grammar.productions.values())
                
                comp_col1, comp_col2 = st.columns(2)
                with comp_col1:
                    st.write("**Gramática Original:**")
                    st.write(f"• No terminales: {len(original_grammar.non_terminals)}")
                    st.write(f"• Terminales: {len(original_grammar.terminals)}")
                    st.write(f"• Producciones: {orig_total}")
                
                with comp_col2:
                    st.write("**Gramática en CNF:**")
                    st.write(f"• No terminales: {len(cnf_grammar.non_terminals)}")
                    st.write(f"• Terminales: {len(cnf_grammar.terminals)}")
                    st.write(f"• Producciones: {cnf_total}")
                
                factor = cnf_total / orig_total if orig_total > 0 else 0
                st.write(f"**Factor de expansión:** {factor:.2f}x")
        
        with tab4:
            st.write("### 📚 Documentación Técnica")
            
            with st.expander("📖 Algoritmo CYK (Cocke-Younger-Kasami)", expanded=True):
                st.markdown("""
                **Descripción:**
                
                El algoritmo CYK es un algoritmo de programación dinámica que determina si una cadena 
                pertenece a un lenguaje libre de contexto especificado por una gramática en CNF.
                
                **Funcionamiento:**
                1. **Inicialización**: Crear tabla triangular T[i][j] de tamaño n×n
                2. **Fase 1**: Llenar diagonal con producciones A → a
                3. **Fase 2**: Para cada subcadena de longitud k ≥ 2:
                   - Para cada división en posición d: T[i][i+k-1] ← T[i][d] × T[d+1][i+k-1] 
                4. **Resultado**: Verificar si S ∈ T[0][n-1]
                
                **Complejidad:**
                - **Tiempo**: O(n³ × |G|) donde n = longitud entrada, |G| = tamaño gramática
                - **Espacio**: O(n²) para almacenar la tabla triangular
                
                **Ventajas:**
                - Garantiza encontrar todas las derivaciones posibles
                - Permite reconstrucción del parse tree mediante backpointers
                - Funciona para cualquier gramática libre de contexto en CNF
                """)
            
            with st.expander("🔄 Proceso de Conversión a CNF"):
                st.markdown("""
                **Forma Normal de Chomsky (CNF)**
                
                Una gramática está en CNF si todas las producciones tienen la forma:
                - **A → BC** (dos no terminales)
                - **A → a** (un terminal)
                
                **Algoritmo de Conversión (implementado):**
                1. **Eliminar producciones ε**: Remover A → ε, generando combinaciones necesarias
                2. **Eliminar producciones unitarias**: Remover A → B, usando clausura transitiva  
                3. **Eliminar símbolos inútiles**: Remover no-generadores e inalcanzables
                4. **Aumentar gramática**: Si S derivaba ε, añadir S₀ → S | ε
                5. **Binarizar producciones**: Dividir A → α₁α₂...αₖ en producciones binarias
                6. **Separar terminales**: Reemplazar terminales en producciones mixtas
                
                **Correcciones aplicadas:**
                - Clasificación correcta de símbolos (LHS → NT, resto se deriva)
                - Detección de anulables sin falsos positivos
                - Verificación estricta de formato CNF final
                """)
            
            with st.expander("⚙️ Implementación y Decisiones de Diseño"):
                st.markdown("""
                **Estructura del Código:**
                
                - **Grammar**: Clase para representar CFG con clasificación correcta de símbolos
                - **CNFConverter**: Pipeline completo de transformación con pasos verificables
                - **CYKParser**: Algoritmo CYK con tabla triangular y backpointers
                - **UI Streamlit**: Interfaz completa con pruebas automatizadas y descargas
                
                **Características Implementadas:**
                - ✅ Simplificador completo (todos los pasos estándar)
                - ✅ CYK con reconstrucción de parse tree
                - ✅ Medición precisa de tiempo de ejecución
                - ✅ Exportación de CNF y parse trees
                - ✅ Casos de prueba exhaustivos
                - ✅ Validación de entrada y manejo de errores
                
                **Decisiones Técnicas:**
                - Uso de conjuntos (sets) para celdas de tabla CYK (eficiencia O(1) lookup)
                - Backpointers con tuplas (tipo, símbolos, split) para reconstrucción
                - Generación incremental de variables auxiliares (X0, X1, ...)
                - Pipeline modular para cada paso de conversión
                """)
            
            with st.expander("🧪 Casos de Prueba y Validación"):
                st.markdown("""
                **Gramática del Proyecto (PDF):**
                
                **Casos Válidos:**
                - "she eats a cake with a fork" → Estructura S → NP VP, VP → VP PP
                - "the cat drinks the beer" → Uso de determinantes obligatorios
                - "he cuts the meat with a knife" → VP → V NP, PP → P NP
                
                **Casos Inválidos:**
                - "dog eats soup" → Falta determinantes requeridos (Det N, no N solo)
                - "she eat cake" → Error de concordancia + falta Det
                - "beautiful cat eats" → 'beautiful' no está en el vocabulario
                
                **Gramática Aritmética:**
                - "id + id * id" → Precedencia correcta de operadores
                - "( id )" → Manejo de paréntesis
                - "+ id id" → Error: operador sin operando izquierdo
                
                **Cobertura de Tests:**
                - Casos sintácticamente correctos e incorrectos
                - Palabras fuera del vocabulario
                - Cadenas vacías y malformadas
                - Estructuras ambiguas y no ambiguas
                """)
            
            with st.expander("⚙️ Optimizaciones y Rendimiento"):
                st.markdown("""
                **Optimizaciones Implementadas:**
                
                - **Tabla triangular**: Solo se almacenan celdas (i,j) con i ≤ j
                - **Sets para símbolos**: Lookup O(1) en lugar de listas O(n)
                - **Cache de variables terminales**: Evita recrear variables para mismo terminal
                - **Iteradores eficientes**: Evita copias innecesarias de estructuras
                
                **Métricas de Performance:**
                - Tiempo medido solo para fase CYK (sin preprocesamiento)
                - Conteo de celdas llenadas vs total de celdas
                - Estadísticas de expansión gramática original → CNF
                
                **Escalabilidad:**
                - O(n³|G|) teórico mantenido en implementación
                - Memoria O(n²) para tabla + O(|G|) para gramática
                - Límite práctico: ~50 palabras en oración para UI responsiva
                """)
    
    except Exception as e:
        st.error(f"Error crítico en la aplicación: {str(e)}")
        st.write("**Detalles del error:**")
        st.exception(e)

if __name__ == "__main__":
    main()