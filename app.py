from flask import Flask, render_template, request
import json
import os
import random

app = Flask(__name__)

# Archivo donde se guardará el estado del intercambio
DATA_FILE = "estado_intercambio.json"

# Lista actual de participantes SIN AARON
NOMBRES_FAMILIA = [
    "Miguel", "Mamá", "Papá Luis", "Abuelita Maria", "Luis Consentido",
    "Daniela", "Efrain", "Karla", "Mariana",
    "Sandra", "Alejandro", "Brenda"
]


def guardar_estado(estado):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def cargar_estado():
    # Si no existe el archivo, se crea uno desde cero
    if not os.path.exists(DATA_FILE):
        estado_inicial = {
            "participantes": NOMBRES_FAMILIA,
            "asignaciones": {}
        }
        guardar_estado(estado_inicial)
        return estado_inicial

    # Leer archivo existente
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        estado = json.load(f)

    # 🔥 SINCRONIZACIÓN AUTOMÁTICA:
    # Si la lista del archivo es distinta a la actual, la corregimos.
    if estado.get("participantes") != NOMBRES_FAMILIA:

        asignaciones = estado.get("asignaciones", {})

        # Quitar asignaciones de gente que ya no está en la lista
        asignaciones_limpias = {
            quien: a_quien
            for quien, a_quien in asignaciones.items()
            if quien in NOMBRES_FAMILIA and a_quien in NOMBRES_FAMILIA
        }

        estado = {
            "participantes": NOMBRES_FAMILIA,  # nueva lista sin Aaron
            "asignaciones": asignaciones_limpias
        }

        guardar_estado(estado)

    return estado


@app.route("/", methods=["GET", "POST"])
def index():
    estado = cargar_estado()
    participantes = estado["participantes"]
    asignaciones = estado["asignaciones"]

    seleccionado = None
    resultado = None
    mensaje_error = None

    if request.method == "POST":
        seleccionado = request.form.get("nombre")

        if not seleccionado or seleccionado not in participantes:
            mensaje_error = "Selecciona un nombre válido."
        else:
            # Si ya tenía asignación, se respeta la misma
            if seleccionado in asignaciones:
                resultado = asignaciones[seleccionado]
            else:
                # Personas ya asignadas a alguien
                ya_asignados = set(asignaciones.values())

                # Lista de candidatos válidos
                candidatos = [
                    p for p in participantes
                    if p not in ya_asignados and p != seleccionado
                ]

                if not candidatos:
                    mensaje_error = "Ya no hay personas disponibles para asignar."
                else:
                    resultado = random.choice(candidatos)
                    asignaciones[seleccionado] = resultado
                    estado["asignaciones"] = asignaciones
                    guardar_estado(estado)

    return render_template(
        "index.html",
        titulo="El intercambio familiar",
        participantes=participantes,
        seleccionado=seleccionado,
        resultado=resultado,
        error=mensaje_error
    )


@app.route("/admin")
def admin():
    """
    Vista secreta para que tú veas todos los resultados del intercambio.
    No compartas este link con la familia.
    """
    estado = cargar_estado()
    participantes = estado["participantes"]
    asignaciones = estado["asignaciones"]

    ya_jugaron = list(asignaciones.keys())
    faltan_por_jugar = [p for p in participantes if p not in asignaciones]
    ya_fueron_regalo = list(asignaciones.values())
    no_son_regalo = [p for p in participantes if p not in ya_fueron_regalo]

    # Buscar duplicados (alguien asignado dos veces)
    duplicados = list({p for p in participantes if ya_fueron_regalo.count(p) > 1})

    todo_completo = (
        len(asignaciones) == len(participantes)
        and len(ya_fueron_regalo) == len(set(ya_fueron_regalo))
        and len(faltan_por_jugar) == 0
        and len(no_son_regalo) == 0
    )

    return render_template(
        "admin.html",
        titulo="Panel del Intercambio Familiar",
        participantes=participantes,
        asignaciones=asignaciones,
        ya_jugaron=ya_jugaron,
        faltan_por_jugar=faltan_por_jugar,
        ya_fueron_regalo=ya_fueron_regalo,
        no_son_regalo=no_son_regalo,
        duplicados=duplicados,
        todo_completo=todo_completo
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
