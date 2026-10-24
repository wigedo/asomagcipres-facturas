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
@app.route("/consultar", methods=["POST"])
def index_o_consultar():
    # Si es una visita normal (GET), muestra la página de inicio
    if request.method == "GET":
        return render_template("index.html")

    # Si es una consulta (POST), procesamos la búsqueda
    codigo_usuario = request.form.get("codigo")

    if not codigo_usuario or not codigo_usuario.strip():
        return render_template(
            "estado_cuenta.html",
            error="Por favor, ingresa un código o número de documento válido."
        )

    codigo_usuario = codigo_usuario.strip()
    conexion = obtener_conexion()
    
    if not conexion:
        return render_template(
            "estado_cuenta.html",
            error="Error en el servidor: No se encontró el archivo de la base de datos ('acueducto_veredal.db')."
        )

    try:
        cursor = conexion.cursor()

        # Inspeccionar las columnas de la tabla suscriptores
        cursor.execute("PRAGMA table_info(suscriptores)")
        columnas = [col[1] for col in cursor.fetchall()]

        condiciones = []
        valores = []

        # 1. Buscar por número de documento exacto
        if "numero_documento" in columnas:
            condiciones.append("numero_documento = ?")
            valores.append(codigo_usuario)

        # 2. Buscar por columnas de código alternativas
        for col in ["codigo", "codigo_suscriptor", "cedula"]:
            if col in columnas:
                condiciones.append(f"{col} = ?")
                valores.append(codigo_usuario)

        # 3. Extraer la parte numérica (ej: C00002 -> 2) para buscar por ID o formato numérico
        digitos = "".join(filter(str.isdigit, codigo_usuario))
        if digitos:
            if "id" in columnas:
                condiciones.append("id = ?")
                valores.append(int(digitos))
            for col in ["codigo", "codigo_suscriptor"]:
                if col in columnas:
                    condiciones.append(f"{col} = ?")
                    valores.append(digitos)
                    condiciones.append(f"{col} = ?")
                    valores.append(f"C{int(digitos):05d}")

        if not condiciones:
            condiciones = ["numero_documento = ?"]
            valores = [codigo_usuario]

        query = "SELECT id, nombre_vecino, numero_documento, vereda FROM suscriptores WHERE " + " OR ".join(condiciones)
        cursor.execute(query, tuple(valores))
        suscriptor = cursor.fetchone()

        if not suscriptor:
            conexion.close()
            return render_template(
                "estado_cuenta.html",
                error=f"No se encontró ningún usuario con el código o documento '{codigo_usuario}'."
            )

        id_s, nombre, documento, vereda = suscriptor

        # Buscar la última factura generada para este suscriptor
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
        tiene_factura = False

        if factura:
            factura_id, fecha_factura, metodo_pago = factura
            factura_num = f"F{factura_id:06d}"

            # Consultar los detalles de los conceptos de esa factura
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

        # Enviar los resultados a la plantilla estado_cuenta.html
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
            tiene_factura=tiene_factura,
        )

    except Exception as e:
        if conexion:
            conexion.close()
        return render_template(
            "estado_cuenta.html",
            error=f"Ocurrió un error al consultar la base de datos: {str(e)}"
        )


if __name__ == "__main__":
    app.run(debug=True)
