# Proyecto No. 2 – Algoritmo CYK (Cocke-Younger-Kasami)

**Curso:** Teoría de la Computación

**Sección:** 20

**Estudiantes:** Pablo Daniel Barillas Moreno Carné No. 22193 & Hugo Daniel Barillas Ajin Carné No. 23556

**Profesor:** Ing. Bidkar Pojoy

> Nota: Repositorio en modo **público**.

---

## Índice

* [Descripción](#descripción)
* [Características](#características)
* [Estructura del repositorio](#estructura-del-repositorio)
* [Requisitos e instalación](#requisitos-e-instalación)
* [Ejecución](#ejecución)
* [Uso paso a paso](#uso-paso-a-paso)
* [Gramáticas incluidas y formato de entrada](#gramáticas-incluidas-y-formato-de-entrada)
* [Arquitectura del código](#arquitectura-del-código)
* [Conversión a CNF (pipeline exacto del código)](#conversión-a-cnf-pipeline-exacto-del-código)
* [Algoritmo CYK y reconstrucción del árbol](#algoritmo-cyk-y-reconstrucción-del-árbol)
* [Exportaciones (CNF / Parse Tree .txt / .dot)](#exportaciones-cnf--parse-tree-txt--dot)
* [Casos de prueba automatizados](#casos-de-prueba-automatizados)
* [Estadísticas y rendimiento](#estadísticas-y-rendimiento)
* [Solución de problemas](#solución-de-problemas)
* [Límites conocidos](#límites-conocidos)
* [Ideas de mejora](#ideas-de-mejora)
* [Licencia](#licencia)
* [Referencias](#referencias)

---

## Descripción

Aplicación interactiva en **Streamlit** que:

1. **Carga** una gramática libre de contexto (CFG).
2. **Simplifica y convierte** la CFG a **Forma Normal de Chomsky (CNF)**.
3. **Ejecuta CYK** (programación dinámica) para decidir si una cadena **pertenece al lenguaje**.
4. **Reconstruye** un **árbol de derivación** (parse tree) a partir de backpointers.
5. **Exporta** CNF y árboles a texto y **DOT** (Graphviz).
6. Incluye **casos de prueba automatizados** y **estadísticas** de la tabla CYK.

Todo el flujo (incluidos los pasos del convertidor a CNF) se **muestra y explica** en la UI con `st.write`, `st.code`, métricas y tablas.

---

## Características

* **CNF completa**: eliminación de ε, unitarias, símbolos **no generadores** e **inalcanzables**, aumento del símbolo inicial si correspondía, binarización y separación de terminales en reglas mixtas.
* **CYK optimizado**:

  * Índice inverso para **A→a** (`terminal_index`) y **A→BC** (`binary_index`) para reducir el factor `|G|`.
  * Tabla triangular con **sets** (`O(1)` lookups) y **backpointers**.
* **Gramáticas integradas**: “Proyecto (PDF)” y “Aritmética”; además, **carga desde texto**.
* **Análisis visual**: tabla CYK como `DataFrame`, conteo de celdas llenas y porcentaje de llenado.
* **Exportación**: CNF (`.txt`), árbol (`.txt` y `.dot`).
* **Manejo de casos edge**: cadena vacía, tokens desconocidos, verificación formal de CNF.

---

## Estructura del repositorio

```
.
├─ CYK_Algorithm_Implementation.py     # App principal: CFG → CNF → CYK → Parse Tree
├─ requirements.txt                    # Dependencias (Streamlit, pandas)
├─ .gitignore                          # Ignora .venv, __pycache__, etc.
├─ Proyecto No 2.pdf                   # Instrucciones del proyecto #2
├─ Ejemplo Proyecto 2.pdf              # Ejemplo teorico de como debe ser el proyecto #2
├─ CNF.txt                             # Ejemplos de las gramáticas usadas, la que no está en CNF y la que si está en CNF.
├─ No_CNF.txt                          # Ejemplos de las gramáticas usadas, la que si está en CNF.
├─ LICENSE                             # MIT
└─ README.md                           # Este archivo
```

---

## Requisitos e instalación

* **Python** 3.9+ (recomendado 3.10 o 3.11)
* **pip** actualizado
* **Graphviz** (opcional, para renderizar `.dot` a imagen con `dot`)

`requirements.txt`:

```
streamlit==1.28.0
pandas==2.1.0
```

Instalación recomendada en entorno virtual:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

> Para DOT: instala Graphviz desde [https://graphviz.org/download/](https://graphviz.org/download/) y asegúrate de que `dot` esté en el PATH.

---

## Ejecución

```bash
streamlit run CYK_Algorithm_Implementation.py
```

La app abre en `http://localhost:8501`.

**(Opcional) Docker**

```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY CYK_Algorithm_Implementation.py .
EXPOSE 8501
CMD ["streamlit", "run", "CYK_Algorithm_Implementation.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

Ejecuta:

```bash
docker build -t cyk-app .
docker run -p 8501:8501 cyk-app
```

---

## Uso paso a paso

1. **Selecciona gramática**

   * *Gramática del Proyecto (PDF)*
   * *Gramática Aritmética*
   * *Cargar desde Texto*

2. **Analiza una oración/expresión** (tab **“🔍 Análisis Individual”**)

   * Ingresa la cadena y presiona **“🚀 Analizar con CYK”**.
   * Se muestran:

     * **Conversión a CNF** paso a paso (ε, unitarias, inútiles, aumento de `S` si aplica, binarización…).
     * **Tabla CYK** triangular (DataFrame).
     * **Resultado** SÍ/NO + **tiempo CYK**.
     * **Árbol de derivación** + descargas.

3. **Casos de prueba** (tab **“🧪 Casos de Prueba”**)

   * Ejecuta batería PASS/FAIL y un **test especial** para gramática con **ε**.

4. **Estadísticas** (tab **“📊 Estadísticas”**)

   * Conteos de **A→a**, **A→BC**, **factor de expansión** de reglas (original vs CNF), etc.

5. **Documentación** (tab **“📚 Documentación”**)

   * Resumen teórico y decisiones de diseño.

---

## Gramáticas incluidas y formato de entrada

### 1) Gramática del Proyecto (PDF)

```
S  → NP VP
VP → VP PP | V NP | cooks | drinks | eats | cuts
PP → P NP
NP → Det N | he | she
V  → cooks | drinks | eats | cuts
P  → in | with
N  → cat | dog | beer | cake | juice | meat | soup | fork | knife | oven | spoon
Det→ a | the
```

### 2) Gramática Aritmética

```
E → E + T | T
T → T * F | F
F → ( E ) | id
```

### 3) Carga desde texto (en la UI)

* Formato: `A -> α | β | ...` (una producción por línea).
* Epsilon aceptado como `ε`, `e` o `epsilon` (se normaliza a `ε`).
* Ejemplo del *placeholder* por defecto (resumen mínimo del proyecto):

  ```
  S -> NP VP
  VP -> VP PP | V NP | cooks | drinks | eats
  PP -> P NP
  NP -> Det N | he | she
  V  -> cooks | drinks | eats
  P  -> in | with
  N  -> cat | beer | cake | fork
  Det-> a | the
  ```

> La clase `Grammar.recompute_symbol_sets()` marca como **terminal** a todo símbolo que **no** aparece como LHS (**no terminal**). Procura usar mayúsculas para NT y minúsculas para terminales.

---

## Arquitectura del código

* **`class Grammar`**

  * `productions: Dict[str, List[List[str]]]`
  * `non_terminals: Set[str]`, `terminals: Set[str]`, `start_symbol = 'S'`
  * `add_production(lhs, rhs)`: valida y agrega; LHS se marca NT.
  * `recompute_symbol_sets()`: recalcula terminales (todo símbolo RHS que no es NT).
  * `display_grammar()`, `to_text_format()`
  * `validate()`: chequea gramática no vacía, presencia de `S`, y NTs referenciados definidos.

* **`class CNFConverter`**

  * Mantiene `original_S_was_nullable` y contador `X0, X1, …` para nuevas variables.
  * Pasos: `eliminate_epsilon()`, `eliminate_unit_productions()`, `remove_useless_symbols()`, `augment_start_if_nullable()`, `convert_to_cnf()`.
  * `_generate_combinations(...)` y `_convert_long_production(...)` para combinatoria y binarización.
  * `convert()`: orquesta todo el pipeline, imprime el estado intermedio y final.

* **`class CYKParser`**

  * Índices inversos:

    * `terminal_index[a] = {A | A→a}`
    * `binary_index[(B,C)] = {A | A→BC}`
  * `parse(sentence)`: tokeniza, llena la tabla (diagonal y superiores), mide tiempo, y devuelve `(accepted, exec_time, parse_tree_text, stats_dict)`.
  * `display_table()`: DataFrame con celdas `∅`/lista de NTs y métricas de llenado.
  * Árbol: `_build_parse_tree(symbol, i, j, indent=0)`.

* **Helpers**

  * `load_grammar_from_text(text)`
  * `create_project_grammar()`, `create_arithmetic_grammar()`
  * `generate_dot_tree(parse_tree, sentence)` → genera `.dot`
  * `verify_cnf_format(grammar)` → verificación estricta de CNF
  * `run_test_cases(parser)` → tabla PASS/FAIL

* **`main()`**: compone la UI (tabs: análisis, pruebas, estadísticas, documentación).

---

## Conversión a CNF (pipeline exacto del código)

1. **ε-producciones** (`eliminate_epsilon`)

   * Detecta **nullable** por iteración (hasta 100); elimina reglas `→ ε` (excepto posible `S` tras aumento) y genera **todas las combinaciones** quitando NTs anulables (sin duplicados).
   * Marca si `S` era anulable (`original_S_was_nullable = True`).

2. **Unitarias** (`eliminate_unit_productions`)

   * Detecta pares `(A,B)` con `A→B`; cierra transitivamente la relación; agrega a `A` las reglas **no unitarias** de `B`; filtra reglas vacías.

3. **Símbolos inútiles** (`remove_useless_symbols`)

   * **No generadores**: solo se conservan reglas cuyo RHS es todo terminal o generador; filtra LHS no generadores.
   * **Inalcanzables**: desde `S`, via BFS; elimina los no alcanzables.
   * Actualiza `non_terminals` = claves actuales de `productions`.

4. **Aumento de `S`** (`augment_start_if_nullable`)

   * Si `S` era nullable: crea `S0 → S | ε`, `start_symbol = 'S0'`.

5. **CNF final** (`convert_to_cnf`)

   * **A→a**: permite `ε` **solo** si `lhs` es el **símbolo inicial**; si `lhs ≠ start_symbol` y `rhs=ε`, se **descarta**.
   * **A→BC**: si aparece un terminal en binaria, introduce variable auxiliar `Xk → a` y reemplaza.
   * **Longitud >2**: binariza recursivamente con nuevas variables `Xk`.
   * Vuelve a filtrar reglas vacías; actualiza `non_terminals`.

> Al final, `verify_cnf_format` comprueba que **solo** existan **A→a**, **A→BC** (y opcionalmente `S→ε`).

---

## Algoritmo CYK y reconstrucción del árbol

* **Inicialización**: `T[i][j]` es un `set` de NTs que generan `w[i..j]`.
* **Fase 1 (diagonal)**: para cada token `w[j]`, inserta todos los `A` con `A→w[j]` usando `terminal_index`.
* **Fase 2 (no diagonal)**: para cada `length`, `i`, `j`, y corte `k`, combina `B∈T[i][k]` y `C∈T[k+1][j]`; con `binary_index[(B,C)]` agrega los `A`.
* **Aceptación**: si `start_symbol ∈ T[0][n-1]`.
* **Árbol**: `_build_parse_tree` sigue el **primer backpointer** almacenado por celda para reconstruir una derivación.
* **Cadena vacía**: si `n=0`, acepta solo si el start tiene `→ ε`.

---

## Exportaciones (CNF / Parse Tree .txt / .dot)

* **CNF**: botón **“⬇️ Descargar CNF como .txt”** produce `grammar_cnf.txt` (una producción por línea `A -> α`).
* **Árbol**:

  * `parse_tree.txt`: árbol en texto, indentado.
  * `parse_tree.dot`: generado por `generate_dot_tree(...)`.

    * Render a imagen:

      ```bash
      dot -Tpng parse_tree.dot -o tree.png
      ```

---

## Casos de prueba automatizados

En **🧪 Casos de Prueba**:

* **Batería principal** (resumen):

  * **Válidos**:
    `she eats a cake with a fork`
    `the cat drinks the beer`
    `he cuts the meat with a knife`
    `a dog eats the soup`
    `she drinks the juice in the oven`
    `the cat cooks`
    `he drinks the beer with the fork`
  * **Inválidos**:
    `she eat cake`
    `the drinks beer`
    `cat the eats`
    `with fork eats she`
    `she`
    `""` (vacía)
    `dog eats soup`
    `she cuts meat`
    `beautiful cat eats`

* **Test especial ε**
  Gramática: `S→A`, `A→a | ε`.
  Se prueba `""` y `"a"` tras pasar por el mismo pipeline CNF.

La UI muestra **PASS/FAIL**, tiempos y **% de éxito**.

---

## Estadísticas y rendimiento

* En **📊 Estadísticas**:

  * Conteo de **no terminales**, **terminales**.
  * Número de producciones totales y separadas por **A→a** y **A→BC**.
  * **Factor de expansión** (reglas originales vs CNF).
  * **Complejidad teórica**:
    Tiempo `O(n³·|G|)`, espacio `O(n²)`.

* En la tabla CYK:

  * **Celdas llenadas**, **total de celdas** y **% de llenado**.

**Optimizaciones reflejadas en el código**:

* Índices inversos (`terminal_index`, `binary_index`).
* `set()` por celda para lookups `O(1)`.
* Reutilización de variables auxiliares para terminales en binarias.

---

## Solución de problemas

* **“Palabras no reconocidas por la gramática”**
  La app lista los tokens desconocidos y muestra el **vocabulario válido** (terminales de tipo `A→a` en la CNF). Ajusta tu entrada o la gramática.
* **Cadena vacía**
  Solo se acepta si el **símbolo inicial** tiene `→ ε` tras el pipeline.
* **No aparece el árbol**
  Ocurre si la oración no es aceptada o no hay backpointer para `start_symbol` en `T[0][n-1]`.
* **`dot` no encontrado**
  Instala Graphviz y agrega `dot` al PATH.
* **Módulos faltantes**
  Ejecuta: `pip install -r requirements.txt`.
* **La app no abre el navegador**
  Abre manualmente `http://localhost:8501`.

---

## Licencia

Este proyecto se distribuye bajo la **Licencia MIT**. Ver `LICENSE`.

---

## Referencias

Aho, A. V., Lam, M. S., Sethi, R., & Ullman, J. D. (2006). *Compilers: Principles, Techniques, & Tools* (2nd ed.). Pearson. [https://mrce.in/ebooks/Compilers%20Principles%2C%20Techniques%2C%20%26%20Tools%202nd%20Ed.pdf](https://mrce.in/ebooks/Compilers%20Principles%2C%20Techniques%2C%20%26%20Tools%202nd%20Ed.pdf)

Cocke, J., & Schwartz, J. T. (1970). *Programming languages and their compilers: Preliminary notes*. New York University. (Descripción general). [https://en.wikipedia.org/wiki/Programming\_Languages\_and\_Their\_Compilers](https://en.wikipedia.org/wiki/Programming_Languages_and_Their_Compilers)

Graphviz Authors. (n.d.). *Graphviz documentation*. [https://graphviz.org/documentation/](https://graphviz.org/documentation/)

Pandas Development Team. (2024). *User guide* (v2.2.3). [https://pandas.pydata.org/docs/user\_guide/index.html](https://pandas.pydata.org/docs/user_guide/index.html)

Streamlit. (n.d.). *Session state*. [https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session\_state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)

Streamlit. (n.d.). *st.text\_input*. [https://docs.streamlit.io/develop/api-reference/widgets/st.text\_input](https://docs.streamlit.io/develop/api-reference/widgets/st.text_input)

Wikipedia contributors. (n.d.). *Chomsky normal form*. In *Wikipedia*. [https://en.wikipedia.org/wiki/Chomsky\_normal\_form](https://en.wikipedia.org/wiki/Chomsky_normal_form)

Wikipedia contributors. (n.d.). *Introduction to Automata Theory, Languages, and Computation*. In *Wikipedia*. [https://en.wikipedia.org/wiki/Introduction\_to\_Automata\_Theory,\_Languages,\_and\_Computation](https://en.wikipedia.org/wiki/Introduction_to_Automata_Theory,_Languages,_and_Computation)

Wikipedia contributors. (n.d.). *Teoría de la computación*. In *Wikipedia*. [https://es.wikipedia.org/wiki/Teor%C3%ADa\_de\_la\_computaci%C3%B3n](https://es.wikipedia.org/wiki/Teor%C3%ADa_de_la_computaci%C3%B3n)

Wikipedia contributors. (n.d.). *Jacob T. Schwartz*. In *Wikipedia*. [https://en.wikipedia.org/wiki/Jacob\_T.\_Schwartz](https://en.wikipedia.org/wiki/Jacob_T._Schwartz)

Younger, D. H. (1967). Recognition and parsing of context-free languages in time n³. *Information and Control, 10*(2), 189–208. [https://doi.org/10.1016/S0019-9958(67)80007-X](https://doi.org/10.1016/S0019-9958%2867%2980007-X)

> Revisión general sobre *parsing* de CFLs:

> *Parsing of context-free languages*. (n.d.). SpringerLink. [https://link.springer.com/chapter/10.1007/978-3-662-07675-0\_2](https://link.springer.com/chapter/10.1007/978-3-662-07675-0_2)

---

> **Video de demostración (no listado):**

---

> **Informe (Revisar a continuación):**