import os
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

# Función para verificar y conectar a la base de datos de forma segura
def obtener_conexion():
    db_path = "acueducto_veredal.db"
    if not os.path.exists(db_path):
        return None
    return sqlite3.connect(db_path)


@app.route("/")
def index():
    # Página principal o buscador
    return render_template("index.html")


@app.route("/consultar", methods=["POST"])
def consultar_estado_cuenta():
    # Obtener el código de forma segura por si viene vacío
    codigo_usuario = request.form.get("codigo")

    if not codigo_usuario or not codigo_usuario.strip():
        return render_template(
            "estado_cuenta.html",
            error="Por favor, ingresa un número de documento o código válido.",
        )

    codigo_usuario = codigo_usuario.strip()

    conexion = obtener_conexion()
    if not conexion:
        return render_template(
            "estado_cuenta.html",
            error="Error en el servidor: No se encontró el archivo de la base de datos ('acueducto_veredal.db').",
        )

    try:
        cursor = conexion.cursor()

        # 1. Buscar al suscriptor por su código o documento
        cursor.execute(
            "SELECT id, nombre_vecino, numero_documento, vereda FROM suscriptores WHERE numero_documento = ?",
            (codigo_usuario,),
        )
        suscriptor = cursor.fetchone()

        if not suscriptor:
            conexion.close()
            return render_template(
                "estado_cuenta.html",
                error="No se encontró ningún usuario con ese código o documento.",
            )

        id_s, nombre, documento, vereda = suscriptor

        # 2. Buscar la última factura generada para este suscriptor
        cursor.execute(
            "SELECT id, fecha, metodo_pago FROM facturas WHERE id_suscriptor = ? ORDER BY id DESC LIMIT 1",
            (id_s,),
        )
        factura = cursor.fetchone()

        items = []
        total_factura = 0
        factura_num = None
        fecha_factura = None
        metodo_pago = None

        if factura:
            factura_id, fecha_factura, metodo_pago = factura
            factura_num = f"F{factura_id:06d}"

            # 3. Consultar los detalles de los conceptos de esa factura
            cursor.execute(
                "SELECT codigo_concepto, concepto, valor FROM detalle_factura WHERE id_factura = ?",
                (factura_id,),
            )
            detalles = cursor.fetchall()

            for cod, concepto, valor in detalles:
                # Aplicar la regla: abonos y amortizaciones restan, los demás suman
                if cod in ["10001", "10008"]:
                    total_factura -= valor
                else:
                    total_factura += valor
                items.append((cod, concepto, valor))

        conexion.close()

        # 4. Enviar los datos calculados a la plantilla HTML (estado_cuenta.html)
        return render_template(
            "estado_cuenta.html",
            nombre=nombre,
            documento=documento,
            vereda=vereda,
            factura_num=factura_num,
            fecha_factura=fecha_factura,
            metodo_pago=metodo_pago,
            items=items,
            total_factura=total_factura,
            tiene_factura=bool(factura),
        )

    except Exception as e:
        if conexion:
            conexion.close()
        return render_template(
            "estado_cuenta.html",
            error=f"Ocurrió un error al consultar la base de datos: {str(e)}",
        )


if __name__ == "__main__":
    app.run(debug=True)