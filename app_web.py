import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)


# Asegurar que las tablas existan al iniciar la aplicación en la nube
def inicializar_bd():
  conexion = sqlite3.connect("acueducto_veredal.db")
  cursor = conexion.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS suscriptores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_vecino TEXT NOT NULL,
            numero_documento TEXT NOT NULL UNIQUE,
            vereda TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_suscriptor INTEGER,
            metodo_pago TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(id_suscriptor) REFERENCES suscriptores(id)
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_factura (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_factura INTEGER,
            codigo_concepto TEXT,
            concepto TEXT,
            valor REAL,
            FOREIGN KEY(id_factura) REFERENCES facturas(id)
        )
    """)
  conexion.commit()
  conexion.close()


inicializar_bd()


def conectar_db():
  return sqlite3.connect("acueducto_veredal.db")


def procesar_consulta_codigo(codigo_usuario):
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
      return {
          "error": "No se encontró ningún usuario con ese código.",
          "nombre": "",
          "documento": codigo_usuario,
          "vereda": "",
          "factura_num": "",
          "fecha_factura": "",
          "metodo_pago": "",
          "items": [],
          "total_factura": 0,
          "tiene_factura": False,
      }

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
        "error": None,
        "nombre": nombre,
        "documento": documento,
        "vereda": vereda,
        "factura_num": factura_num,
        "fecha_factura": fecha_factura,
        "metodo_pago": metodo_pago,
        "items": items,
        "total_factura": total_factura,
        "tiene_factura": bool(factura),
    }
  except Exception as e:
    return {
        "error": f"Error en la base de datos: {e}",
        "nombre": "",
        "documento": "",
        "vereda": "",
        "factura_num": "",
        "fecha_factura": "",
        "metodo_pago": "",
        "items": [],
        "total_factura": 0,
        "tiene_factura": False,
    }


@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    codigo = request.form.get("codigo", "").strip()
    datos = procesar_consulta_codigo(codigo)
    return render_template("estado_cuenta.html", **datos)
  return render_template("index.html")


@app.route("/consultar", methods=["POST"])
def consultar_estado_cuenta():
  codigo = request.form.get("codigo", "").strip()
  datos = procesar_consulta_codigo(codigo)
  return render_template("estado_cuenta.html", **datos)


if __name__ == "__main__":
  app.run(debug=True)
