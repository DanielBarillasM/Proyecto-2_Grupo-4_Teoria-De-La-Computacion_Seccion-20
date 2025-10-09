from grammar import Grammar

def load_grammar_from_text(text: str) -> Grammar:
    """Carga una gramática desde texto (formato A -> α | β)."""
    grammar = Grammar()
    lines = (text or "").strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '->' in line:
            lhs, rhs_text = [p.strip() for p in line.split('->', 1)]
            alts = [alt.strip() for alt in rhs_text.split('|')] if '|' in rhs_text else [rhs_text]
            for alt in alts:
                if alt:
                    rhs = ['ε' if s in ('e', 'epsilon') else s for s in alt.split()]
                    grammar.add_production(lhs, rhs)
    grammar.recompute_symbol_sets()
    return grammar

def create_project_grammar() -> Grammar:
    """Gramática del proyecto (PDF)."""
    g = Grammar()
    g.add_production('S', ['NP', 'VP'])

    g.add_production('VP', ['VP', 'PP'])
    g.add_production('VP', ['V', 'NP'])
    g.add_production('VP', ['cooks'])
    g.add_production('VP', ['drinks'])
    g.add_production('VP', ['eats'])
    g.add_production('VP', ['cuts'])

    g.add_production('PP', ['P', 'NP'])

    g.add_production('NP', ['Det', 'N'])
    g.add_production('NP', ['he'])
    g.add_production('NP', ['she'])

    g.add_production('V', ['cooks'])
    g.add_production('V', ['drinks'])
    g.add_production('V', ['eats'])
    g.add_production('V', ['cuts'])

    g.add_production('P', ['in'])
    g.add_production('P', ['with'])

    for n in ['cat','dog','beer','cake','juice','meat','soup','fork','knife','oven','spoon']:
        g.add_production('N', [n])

    g.add_production('Det', ['a'])
    g.add_production('Det', ['the'])

    g.recompute_symbol_sets()
    return g

def create_arithmetic_grammar() -> Grammar:
    """Gramática aritmética básica."""
    g = Grammar()
    g.add_production('E', ['E', '+', 'T'])
    g.add_production('E', ['T'])
    g.add_production('T', ['T', '*', 'F'])
    g.add_production('T', ['F'])
    g.add_production('F', ['(', 'E', ')'])
    g.add_production('F', ['id'])
    g.recompute_symbol_sets()
    return g