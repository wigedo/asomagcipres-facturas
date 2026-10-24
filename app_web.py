import os
import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

def obtener_conexion():
    db_path = "acueducto_veredal.db"
    if not os.path.exists(db_path):
        return None
    return sqlite3.connect(db_path)


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    suscriptor = None
    nombre = None
    documento = None
    vereda = None
    factura_num = None
    fecha_factura = None
    metodo_pago = None
    items = []
    total_factura = 0
    tiene_factura = False

    # Si el usuario envió el formulario de búsqueda
    if request.method == "POST":
        codigo_usuario = request.form.get("codigo")

        if not codigo_usuario or not codigo_usuario.strip():
            error = "Por favor, ingresa un número de documento o código válido."
        else:
            codigo_usuario = codigo_usuario.strip()
            conexion = obtener_conexion()
            
            if not conexion:
                error = "Error en el servidor: No se encontró el archivo de la base de datos ('acueducto_veredal.db')."
            else:
                try:
                    cursor = conexion.cursor()

                    # 1. Buscar al suscriptor por documento
                    cursor.execute(
                        "SELECT id, nombre_vecino, numero_documento, vereda FROM suscriptores WHERE numero_documento = ?",
                        (codigo_usuario,),
                    )
                    suscriptor = cursor.fetchone()

                    if not suscriptor:
                        error = "No se encontró ningún usuario con ese documento."
                    else:
                        id_s, nombre, documento, vereda = suscriptor

                        # 2. Buscar la última factura generada
                        cursor.execute(
                            "SELECT id, fecha, metodo_pago FROM facturas WHERE id_suscriptor = ? ORDER BY id DESC LIMIT 1",
                            (id_s,),
                        )
                        factura = cursor.fetchone()

                        if factura:
                            factura_id, fecha_factura, metodo_pago = factura
                            factura_num = f"F{factura_id:06d}"

                            # 3. Consultar los detalles de los conceptos
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
                            
                            tiene_factura = True

                    conexion.close()
                except Exception as e:
                    if conexion:
                        conexion.close()
                    error = f"Ocurrió un error al consultar la base de datos: {str(e)}"

    return render_template(
        "index.html",
        error=error,
        nombre=nombre,
        documento=documento,
        vereda=vereda,
        factura_num=factura_num,
        fecha_factura=fecha_factura,
        metodo_pago=metodo_pago,
        items=items,
        total_factura=total_factura,
        tiene_factura=tiene_factura,
    )


if __name__ == "__main__":
    app.run(debug=True)
