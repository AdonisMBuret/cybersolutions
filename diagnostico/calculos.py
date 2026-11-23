from collections.abc import Sequence


def calcular_resultado(respuestas: Sequence[bool]) -> dict[str, int | str]:
    if len(respuestas) != 6 or any(type(respuesta) is not bool for respuesta in respuestas):
        raise ValueError("El cálculo requiere seis respuestas booleanas.")

    indice_proteccion = sum(respuestas)
    if indice_proteccion <= 2:
        nivel_riesgo = "ALTO"
        nombre_paquete = "Completo"
    elif indice_proteccion <= 4:
        nivel_riesgo = "MEDIO"
        nombre_paquete = "Intermedio"
    else:
        nivel_riesgo = "BAJO"
        nombre_paquete = "Básico"

    return {
        "indice_proteccion": indice_proteccion,
        "nivel_riesgo": nivel_riesgo,
        "nombre_paquete": nombre_paquete,
    }
