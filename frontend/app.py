# --- habilitar imports planos desde backend/ ---
import os, sys
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(CURRENT_DIR, '..', 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# --- imports normales ---
import streamlit as st
import pandas as pd

from grammar import Grammar
from grammars import create_project_grammar, create_arithmetic_grammar, load_grammar_from_text
from cnf_converter import CNFConverter
from cyk import CYKParser
from utils import verify_cnf_format, generate_dot_tree
from tests import run_test_cases


# ---- Logger que traduce niveles a Streamlit ----
def st_logger(level: str, msg: str) -> None:
    if level == "code":
        st.code(msg)
    elif level == "success":
        st.success(msg)
    elif level == "warning":
        st.warning(msg)
    elif level == "error":
        st.error(msg)
    else:
        st.write(msg)


# ---- Helpers de UI ----
def render_cyk_table(words, table):
    """Construye y muestra la tabla CYK como DataFrame (triangular superior)."""
    n = len(words)
    headers = [f"w{i+1}={words[i]}" for i in range(n)]
    data = []
    for i in range(n - 1, -1, -1):  # fila superior = subcadenas largas
        row = []
        for j in range(n):
            if j >= i:
                content = ", ".join(sorted(table[i][j])) if table[i][j] else "∅"
                row.append(content)
            else:
                row.append("")
        data.append(row)
    df = pd.DataFrame(data, columns=headers, index=[f"Nivel {i+1}" for i in range(n)])
    st.dataframe(df, use_container_width=True)


# ---- Página ----
st.set_page_config(page_title="Algoritmo CYK - Teoría de la Computación", page_icon="🔍", layout="wide")
st.title("🔍 Implementación del Algoritmo CYK")
st.markdown("**Teoría de la Computación 2024 - Proyecto 2**")
st.markdown("*CFG → CNF → CYK con reconstrucción de parse tree*")

with st.expander("📋 Información del Proyecto", expanded=False):
    st.markdown("""
    ### Objetivos Completados:
    - ✅ **Simplificador completo**: ε-producciones, unitarias, símbolos inútiles, CNF
    - ✅ **Algoritmo CYK**: tabla triangular, backpointers, parse tree
    - ✅ **Salidas**: SÍ/NO + tiempo + árbol
    - ✅ **Pruebas**: casos automatizados

    ### Correcciones Aplicadas:
    - 🔧 Clasificación de símbolos (LHS NT)
    - 🔧 Detección de anulables correcta
    - 🔧 Eliminación de símbolos inútiles
    - 🔧 Verificación CNF estricta
    - 🔧 Tests alineados con la gramática del PDF
    """)

# ---- Selección de gramática ----
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
else:
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
    else:
        st.warning("Ingrese una gramática válida")
        st.stop()

# ---- Validación y visualización ----
ok, msg = original_grammar.validate()
if not ok:
    st.error(f"❌ Error en gramática: {msg}")
    st.stop()
st.success(f"✅ {msg}")

with st.expander("Ver Gramática Original"):
    st.code(original_grammar.display_grammar())

# ---- Conversión a CNF ----
st.write("## 🔄 Conversión a Forma Normal de Chomsky")
converter = CNFConverter(original_grammar, log=st_logger)
cnf_grammar, conversion_success = converter.convert()
if not conversion_success:
    st.error("❌ Error en la conversión a CNF. No se puede continuar.")
    st.stop()

is_cnf, cnf_msg = verify_cnf_format(cnf_grammar)
if is_cnf:
    st.success(f"✅ {cnf_msg}")
else:
    st.error(f"❌ {cnf_msg}")
    st.stop()

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
    st.metric("Producciones CNF", sum(len(v) for v in cnf_grammar.productions.values()))

# ---- Parser CYK ----
parser = CYKParser(cnf_grammar, log=st_logger)

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Análisis Individual", "🧪 Casos de Prueba", "📊 Estadísticas", "📚 Documentación"])

with tab1:
    st.write("### Analizador CYK")

    # --- Ejemplos por gramática ---
    if grammar_option == "Gramática del Proyecto (PDF)":
        st.write("#### Ejemplos:")
        c1, c2 = st.columns(2)
        with c1:
            st.write("**✅ Válidas**")
            for ex in [
                "she eats a cake with a fork",
                "the cat drinks the beer",
                "he cuts the meat with a knife",
                "a dog eats the soup",
                "she drinks the juice in the oven",
            ]:
                st.write(f"• {ex}")
        with c2:
            st.write("**❌ Inválidas**")
            for ex in ["she eat cake", "dog eats soup", "cat the eats", "beautiful cat eats", "she cuts meat"]:
                st.write(f"• {ex}")

    elif grammar_option == "Gramática Aritmética":
        st.write("#### Ejemplos:")
        c1, c2 = st.columns(2)
        with c1:
            st.write("**✅ Válidas**")
            for ex in ["id + id * id", "( id )", "id * ( id + id )", "( id + id ) * id"]:
                st.write(f"• {ex}")
        with c2:
            st.write("**❌ Inválidas**")
            for ex in ["id *", "+ id id", "id + + id", "( id"]:
                st.write(f"• {ex}")

    # ========= ENTRADA (corregido para evitar el error de session_state) =========
    default_sentence = (
        "she eats a cake with a fork"
        if grammar_option == "Gramática del Proyecto (PDF)"
        else "id + id * id"
    )

    # 1) inicializa estado ANTES de crear widgets
    if "_grammar_tag" not in st.session_state:
        st.session_state["_grammar_tag"] = grammar_option
    if "sentence" not in st.session_state:
        st.session_state["sentence"] = default_sentence
    if st.session_state["_grammar_tag"] != grammar_option:
        st.session_state["sentence"] = default_sentence
        st.session_state["_grammar_tag"] = grammar_option

    # 2) callback para botones rápidos (se ejecuta ANTES del text_input)
    def _set_sentence(value: str):
        st.session_state["sentence"] = value
        st.rerun()

    # 3) Botones rápidos ANTES del text_input, usando on_click
    if grammar_option == "Gramática del Proyecto (PDF)":
        st.write("**Ejemplos rápidos:**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.button("Ejemplo 1", help="she eats a cake with a fork",
                      on_click=_set_sentence, args=("she eats a cake with a fork",))
        with c2:
            st.button("Ejemplo 2", help="the cat drinks the beer",
                      on_click=_set_sentence, args=("the cat drinks the beer",))
        with c3:
            st.button("VP -> VP PP", help="he cuts the meat with a knife",
                      on_click=_set_sentence, args=("he cuts the meat with a knife",))
        with c4:
            st.button("Oración inválida", help="dog eats soup",
                      on_click=_set_sentence, args=("dog eats soup",))
    else:
        st.write("**Ejemplos rápidos:**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.button("id + id * id", on_click=_set_sentence, args=("id + id * id",))
        with c2:
            st.button("( id )", on_click=_set_sentence, args=("( id )",))
        with c3:
            st.button("id * ( id + id )", on_click=_set_sentence, args=("id * ( id + id )",))
        with c4:
            st.button("inválida: id *", on_click=_set_sentence, args=("id *",))

    # 4) Ahora sí: text_input que usa el valor ya presente en session_state
    sentence = st.text_input(
        "Texto a analizar:",
        key="sentence",
        placeholder=f"Escriba usando las palabras de la {grammar_source.lower()}...",
        help=f"Use solo símbolos definidos en la {grammar_source.lower()}",
    )
    current_sentence = st.session_state["sentence"]
    # =========================================================================

    if st.button("🚀 Analizar con CYK", type="primary", use_container_width=True):
        if current_sentence.strip():
            with st.spinner("Ejecutando algoritmo CYK..."):
                accepted, exec_time, parse_tree, stats = parser.parse(current_sentence)

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.success("✅ **SÍ** - Aceptada por la gramática") if accepted else st.error("❌ **NO** - Rechazada por la gramática")
                with c2:
                    st.info(f"⏱️ **Tiempo CYK:** {exec_time:.6f} seg")
                with c3:
                    if 'error' not in stats:
                        st.metric("📏 Longitud", f"{stats['length']} tokens")

                if 'error' in stats:
                    st.error(f"❌ **Error:** {stats['error']}")
                    if 'unknown_words' in stats:
                        st.write("**Tokens no reconocidos:**", ', '.join(stats['unknown_words']))
                        st.write("**Vocabulario disponible:**")
                        valid_tokens = set()
                        for rhs_list in cnf_grammar.productions.values():
                            for rhs in rhs_list:
                                if len(rhs) == 1 and rhs[0] in cnf_grammar.terminals:
                                    valid_tokens.add(rhs[0])
                        st.write(", ".join(sorted(valid_tokens)))
                else:
                    # Tabla CYK
                    st.write("### Tabla CYK")
                    render_cyk_table(parser.words, parser.table)

                    # Parse tree
                    if parse_tree:
                        st.write("### 🌳 Árbol de Análisis Sintáctico")
                        st.code(parse_tree, language="")
                        dot_code = generate_dot_tree(parse_tree, current_sentence)
                        d1, d2 = st.columns(2)
                        with d1:
                            st.download_button(
                                "⬇️ Descargar Parse Tree (.dot)",
                                dot_code,
                                file_name="parse_tree.dot",
                                mime="text/plain",
                                help="Visualiza con: dot -Tpng parse_tree.dot -o tree.png"
                            )
                        with d2:
                            st.download_button(
                                "⬇️ Descargar Parse Tree (.txt)",
                                parse_tree,
                                file_name="parse_tree.txt",
                                mime="text/plain"
                            )

                        with st.expander("🔍 Análisis del Parse Tree"):
                            tree_lines = [line for line in parse_tree.strip().split('\n') if '→' in line]
                            st.write(f"**Nodos en el árbol:** {len(tree_lines)}")
                            depth = max((len(l) - len(l.lstrip())) // 2 for l in tree_lines) + 1 if tree_lines else 0
                            st.write(f"**Profundidad máxima:** {depth}")

                            def is_terminal_line(line: str) -> bool:
                                rhs = line.split('→', 1)[1].strip().split()
                                return len(rhs) == 1 and (rhs[0] in cnf_grammar.terminals or rhs[0] in {'ε', 'e'})
                            terminals = sum(is_terminal_line(l) for l in tree_lines)
                            non_terminals = len(tree_lines) - terminals
                            st.write(f"**Nodos terminales:** {terminals}")
                            st.write(f"**Nodos no terminales:** {non_terminals}")

                if 'error' not in stats:
                    st.success("🎉 **¡Análisis exitoso!**") if accepted else st.info("ℹ️ La entrada no puede ser generada por esta gramática.")
        else:
            st.warning("⚠️ Por favor ingrese texto para analizar.")

with tab2:
    st.write("### 🧪 Ejecución de Casos de Prueba")
    st.write("Valida automáticamente el funcionamiento del algoritmo con múltiples casos.")

    # Gramática especial con ε para test
    st.write("#### Test Especial: Gramática que acepta cadena vacía")
    epsilon_g = Grammar()
    epsilon_g.add_production('S', ['A'])
    epsilon_g.add_production('A', ['a'])
    epsilon_g.add_production('A', ['ε'])
    epsilon_g.recompute_symbol_sets()

    eps_converter = CNFConverter(epsilon_g, log=st_logger)
    epsilon_cnf, _ = eps_converter.convert()
    epsilon_parser = CYKParser(epsilon_cnf, log=st_logger)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧪 Test cadena vacía", help="Prueba con gramática que acepta ε"):
            accepted, exec_time, parse_tree, _ = epsilon_parser.parse("")
            if accepted:
                st.success(f"✅ Cadena vacía ACEPTADA en {exec_time:.6f}s")
                if parse_tree:
                    st.code(parse_tree)
            else:
                st.error("❌ Cadena vacía RECHAZADA")

    with c2:
        if st.button("🧪 Test 'a' con epsilon", help="Prueba 'a' con gramática que acepta ε"):
            accepted, exec_time, _, _ = epsilon_parser.parse("a")
            st.success(f"✅ 'a' ACEPTADA en {exec_time:.6f}s") if accepted else st.error("❌ 'a' RECHAZADA")

    with st.expander("Ver gramática epsilon en CNF"):
        st.code(epsilon_cnf.display_grammar())

    if st.button("▶️ Ejecutar Todos los Tests", type="secondary"):
        with st.spinner("Ejecutando batería de pruebas..."):
            results = run_test_cases(parser)  # devuelve list[dict]
            st.dataframe(pd.DataFrame(results), use_container_width=True)
            passed = sum(1 for r in results if "PASS" in r["Estado"])
            total = len(results)
            st.metric("Tests Pasados", f"{passed}/{total} ({(passed/total)*100:.1f}%)")

with tab3:
    st.write("### 📊 Análisis de la Gramática y Estadísticas")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("No Terminales", len(cnf_grammar.non_terminals))
        st.metric("Terminales", len(cnf_grammar.terminals))
    with c2:
        total_prods = sum(len(v) for v in cnf_grammar.productions.values())
        st.metric("Producciones", total_prods)
        term_prods = sum(1 for rhs_list in cnf_grammar.productions.values() for rhs in rhs_list if len(rhs) == 1)
        st.metric("Terminales (A→a)", term_prods)
    with c3:
        bin_prods = sum(1 for rhs_list in cnf_grammar.productions.values() for rhs in rhs_list if len(rhs) == 2)
        st.metric("Binarias (A→BC)", bin_prods)
        st.metric("Forma CNF", "✅" if is_cnf else "❌")
    with c4:
        st.write("**Complejidad CYK:**")
        st.write("• Tiempo: O(n³|G|)")
        st.write("• Espacio: O(n²)")
        st.write("• n = longitud entrada")
        st.write("• |G| = tamaño gramática")

    with st.expander("🔍 Producciones CNF (detallado)"):
        terms, bins = [], []
        for lhs, rhs_list in cnf_grammar.productions.items():
            for rhs in rhs_list:
                if len(rhs) == 1:
                    terms.append(f"{lhs} → {rhs[0]}")
                elif len(rhs) == 2:
                    bins.append(f"{lhs} → {rhs[0]} {rhs[1]}")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Producciones A → a ({len(terms)}):**")
            for p in sorted(terms): st.write(f"• {p}")
        with c2:
            st.write(f"**Producciones A → BC ({len(bins)}):**")
            for p in sorted(bins): st.write(f"• {p}")

    with st.expander("📈 Comparación: Original vs CNF"):
        orig_total = sum(len(v) for v in original_grammar.productions.values())
        cnf_total = sum(len(v) for v in cnf_grammar.productions.values())
        cc1, cc2 = st.columns(2)
        with cc1:
            st.write("**Gramática Original:**")
            st.write(f"• No terminales: {len(original_grammar.non_terminals)}")
            st.write(f"• Terminales: {len(original_grammar.terminals)}")
            st.write(f"• Producciones: {orig_total}")
        with cc2:
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
        **Descripción:** Algoritmo de programación dinámica para decidir pertenencia de cadenas a lenguajes CFG en CNF.

        **Funcionamiento:**
        1. Inicialización: tabla T[i][j] de n×n
        2. Diagonal: A → a
        3. Combinaciones: A → BC
        4. Aceptación: S ∈ T[0][n-1]

        **Complejidad:** Tiempo O(n³·|G|), Espacio O(n²)
        """)
    with st.expander("🔄 Proceso de Conversión a CNF"):
        st.markdown("""
        1) Eliminar ε-producciones  
        2) Eliminar unitarias A→B  
        3) Eliminar símbolos no generadores e inalcanzables  
        4) Aumentar start si S⇒*ε  
        5) Binarizar producciones largas  
        6) Separar terminales en binarias
        """)
    with st.expander("⚙️ Decisiones de Diseño"):
        st.markdown("""
        - Backend sin dependencias de UI; logging por callback.
        - Índices inversos (A→a, A→BC) para acelerar CYK.
        - Reconstrucción del árbol con backpointers.
        - Exportaciones a .txt y .dot.
        """)