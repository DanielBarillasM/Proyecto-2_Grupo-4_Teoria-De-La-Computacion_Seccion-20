from typing import Tuple
from grammar import Grammar

def generate_dot_tree(parse_tree: str, sentence: str) -> str:
    """Genera código DOT para el parse tree."""
    def _esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    try:
        lines = (parse_tree or "").strip().split('\n')
        dot = [
            'digraph ParseTree {',
            '    rankdir=TB;',
            '    node [shape=box, style=rounded];',
            '    edge [dir=none];'
        ]
        node_counter = 0
        node_stack = []
        sent_tokens = set((sentence or "").lower().split())

        for line in lines:
            level = len(line) - len(line.lstrip())
            content = line.strip()
            if '→' not in content:
                continue
            lhs, rhs = [p.strip() for p in content.split('→', 1)]
            node_id = f"n{node_counter}"; node_counter += 1
            while len(node_stack) > level // 2:
                node_stack.pop()
            dot.append(f'    {node_id} [label="{_esc(lhs)}", fillcolor=lightblue, style="rounded,filled"];')
            if node_stack:
                dot.append(f'    {node_stack[-1]} -> {node_id};')
            node_stack.append(node_id)

            rhs_tokens = rhs.split()
            is_terminal = (len(rhs_tokens) == 1 and (rhs_tokens[0] in sent_tokens or rhs_tokens[0] in {
                'a','the','he','she','cat','dog','beer','cake','juice','meat','soup','fork','knife','oven','spoon',
                'cooks','drinks','eats','cuts','in','with','id','+','*','(',')','ε','e'
            }))
            if is_terminal and rhs not in ('?', ''):
                leaf_id = f"n{node_counter}"; node_counter += 1
                dot.append(f'    {leaf_id} [label="{_esc(rhs)}", shape=ellipse, fillcolor=lightgreen, style="filled"];')
                dot.append(f'    {node_id} -> {leaf_id};')

        dot.append('}')
        return '\n'.join(dot)
    except Exception as e:
        return f'''digraph ParseTree {{
    node [shape=box];
    error [label="Error generando árbol: {str(e)}", fillcolor=red, style=filled];
}}'''

def verify_cnf_format(grammar: Grammar) -> Tuple[bool, str]:
    """Verifica si la gramática está en CNF estricta (permitiendo S→ε)."""
    try:
        for lhs, rhs_list in grammar.productions.items():
            for rhs in rhs_list:
                if len(rhs) == 1:
                    a = rhs[0]
                    if a in ('ε', 'e'):
                        if lhs == grammar.start_symbol:
                            continue
                        return False, f"Epsilon fuera del símbolo inicial: {lhs} → ε"
                    if a not in grammar.terminals:
                        return False, f"Producción unitaria residual: {lhs} → {a}"
                elif len(rhs) == 2:
                    if rhs[0] in grammar.terminals or rhs[1] in grammar.terminals:
                        return False, f"Producción binaria con terminales: {lhs} → {' '.join(rhs)}"
                else:
                    return False, f"Producción de longitud > 2: {lhs} → {' '.join(rhs)}"
        return True, "Gramática en CNF válida"
    except Exception as e:
        return False, f"Error verificando CNF: {e}"