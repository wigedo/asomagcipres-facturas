import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def index():
  # Aquí se carga tu página principal o buscador (asegúrate de que apunte a tu archivo html principal)
  return render_template("index.html")


@app.route("/consultar", methods=["POST"])
def consultar_estado_cuenta():
  codigo_usuario = request.form.get("codigo").strip()

  conexion = sqlite3.connect("acueducto_veredal.db")
  cursor = conexion.cursor()

  # 1. Buscar al suscriptor por su código o documento
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


if __name__ == "__main__":
  app.run(debug=True)
