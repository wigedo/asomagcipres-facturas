import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)


def conectar_db():
  return sqlite3.connect("acueducto_veredal.db")


def procesar_consulta_codigo(codigo_usuario):
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
    return None, "No se encontró ningún usuario con ese código."

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
      if cod in ["10001", "10008"]:
        total_factura -= valor
      else:
        total_factura += valor
      items.append((cod, concepto, valor))

  conexion.close()

  return {
      "nombre": nombre,
      "documento": documento,
      "vereda": vereda,
      "factura_num": factura_num,
      "fecha_factura": fecha_factura,
      "metodo_pago": metodo_pago,
      "items": items,
      "total_factura": total_factura,
      "tiene_factura": bool(factura),
  }, None


@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    codigo = request.form.get("codigo", "").strip()
    datos, error = procesar_consulta_codigo(codigo)
    if error:
      return render_template("estado_cuenta.html", error=error)
    return render_template("estado_cuenta.html", **datos)
  return render_template("index.html")


@app.route("/consultar", methods=["POST"])
def consultar_estado_cuenta():
  codigo = request.form.get("codigo", "").strip()
  datos, error = procesar_consulta_codigo(codigo)
  if error:
    return render_template("estado_cuenta.html", error=error)
  return render_template("estado_cuenta.html", **datos)


if __name__ == "__main__":
  app.run(debug=True)
