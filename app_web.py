import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)


def conectar_db():
  return sqlite3.connect("acueducto_veredal.db")


@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    codigo_usuario = request.form.get("codigo", "").strip()

    try:
      conexion = conectar_db()
      cursor = conexion.cursor()

      # 1. Buscar al suscriptor por su código
      cursor.execute(
          "SELECT id, nombre_vecino, numero_documento, vereda FROM suscriptores"
          " WHERE numero_documento = ?",
          (codigo_usuario,),
      )
      suscriptor = cursor.fetchone()

      if not suscriptor:
        conexion.close()
        return render_template(
            "estado_cuenta.html",
            error="No se encontró ningún usuario con ese código.",
            tiene_factura=False,
            nombre="",
            documento=codigo_usuario,
            vereda="",
        )

      id_s, nombre, documento, vereda = suscriptor

      # 2. Buscar la última factura generada para este suscriptor
      cursor.execute(
          "SELECT id, fecha, metodo_pago FROM facturas WHERE id_suscriptor = ?"
          " ORDER BY id DESC LIMIT 1",
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
            "SELECT codigo_concepto, concepto, valor FROM detalle_factura WHERE"
            " id_factura = ?",
            (factura_id,),
        )
        detalles = cursor.fetchall()

        for cod, concepto, valor in detalles:
          # Abonos y amortizaciones restan, los demás cargos suman
          if cod in ["10001", "10008"]:
            total_factura -= valor
          else:
            total_factura += valor
          items.append((cod, concepto, valor))

      conexion.close()

      # 4. Enviar los datos completos a la plantilla HTML
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
          error=None,
      )

    except Exception as e:
      return render_template(
          "estado_cuenta.html",
          error=f"Error al procesar la consulta: {e}",
          tiene_factura=False,
          nombre="",
          documento="",
          vereda="",
      )

  return render_template("index.html")


if __name__ == "__main__":
  app.run(debug=True)
