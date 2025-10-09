from typing import List, Dict, Tuple
from cyk import CYKParser

def run_test_cases(parser: CYKParser) -> List[Dict[str, str]]:
    """Ejecuta los casos de prueba y devuelve una lista de dicts (para que el frontend los muestre)."""
    test_cases: List[Tuple[str, bool, str]] = [
        ("she eats a cake with a fork", True, "Ejemplo del PDF"),
        ("the cat drinks the beer", True, "Ejemplo del PDF"),
        ("he cuts the meat with a knife", True, "Estructura similar"),
        ("a dog eats the soup", True, "NP requiere Det + N"),
        ("she drinks the juice in the oven", True, "VP -> VP PP"),
        ("the cat cooks", True, "VP -> verbo solo"),
        ("he drinks the beer with the fork", True, "VP -> VP PP complejo"),
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

    results: List[Dict[str, str]] = []
    for sentence, expected, description in test_cases:
        try:
            accepted, exec_time, _, _ = parser.parse(sentence)
            status = "✅ PASS" if accepted == expected else "❌ FAIL"
            results.append({
                "Oración": sentence if sentence else "(vacía)",
                "Esperado": "SÍ" if expected else "NO",
                "Obtenido": "SÍ" if accepted else "NO",
                "Estado": status,
                "Tiempo (ms)": f"{exec_time*1000:.2f}",
                "Descripción": description
            })
        except Exception as e:
            results.append({
                "Oración": sentence if sentence else "(vacía)",
                "Esperado": "SÍ" if expected else "NO",
                "Obtenido": f"ERROR: {str(e)}",
                "Estado": "❌ ERROR",
                "Tiempo (ms)": "N/A",
                "Descripción": description
            })
    return results