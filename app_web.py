from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)


# Función para conectar a la base de datos existente
def conectar_db():
  return sqlite3.connect("acueducto_veredal.db")


# Ruta principal: Pantalla de inicio de sesión o consulta por código
@app.route("/", methods=["GET", "POST"])
def index():
  error = None
  if request.method == "POST":
    codigo = request.form.get("codigo").strip()

    conexion = conectar_db()
    cursor = conexion.cursor()
    # Verificamos si el usuario existe
    cursor.execute(
        "SELECT id, nombre_vecino, vereda FROM suscriptores WHERE"
        " numero_documento = ?",
        (codigo,),
    )
    usuario = cursor.fetchone()
    conexion.close()

    if usuario:
      # Si existe, lo redirigimos a su historial personal usando su código
      return redirect(url_for("historial", codigo=codigo))
    else:
      error = (
          "Código de usuario no encontrado. Verifique e intente nuevamente."
      )

  return render_template("index.html", error=error)


# Ruta de historial y facturas personales del usuario
@app.route("/historial/<codigo>")
def historial(codigo):
  conexion = conectar_db()
  cursor = conexion.cursor()

  # Buscamos los datos del suscriptor
  cursor.execute(
      "SELECT id, nombre_vecino, numero_documento, vereda FROM suscriptores"
      " WHERE numero_documento = ?",
      (codigo,),
  )
  usuario = cursor.fetchone()

  if not usuario:
    conexion.close()
    return redirect(url_for("index"))

  id_suscriptor = usuario[0]

  # Buscamos todas las facturas de este usuario junto con sus detalles y método de pago
  cursor.execute(
      """
        SELECT f.id, f.fecha, f.metodo_pago, d.codigo_concepto, d.concepto, d.valor
        FROM facturas f
        JOIN detalle_factura d ON f.id = d.id_factura
        WHERE f.id_suscriptor = ?
        ORDER BY f.id DESC
    """,
      (id_suscriptor,),
  )
  resultados = cursor.fetchall()
  conexion.close()

  # Agrupamos los movimientos por factura para mostrarlos ordenados
  facturas_dict = {}
  for row in resultados:
    fact_id, fecha, metodo, cod_con, concepto, valor = row
    if fact_id not in facturas_dict:
      facturas_dict[fact_id] = {
          "fecha": fecha,
          "metodo": metodo,
          "items": [],
          "total": 0,
      }

    # Lógica de suma/resta exacta igual al programa de escritorio
    if cod_con in ["10001", "10008"]:
      valor_neto = -valor
    else:
      valor_neto = valor

    facturas_dict[fact_id]["items"].append(
        {"codigo": cod_con, "concepto": concepto, "valor": valor_neto}
    )
    facturas_dict[fact_id]["total"] += valor_neto

  return render_template(
      "historial.html", usuario=usuario, facturas=facturas_dict
  )


if __name__ == "__main__":
  # Arranca el servidor web localmente en el puerto 5000
  app.run(debug=True, port=5000)