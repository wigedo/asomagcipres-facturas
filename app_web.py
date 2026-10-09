import sqlite3
import traceback
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
  try:
    if request.method == "POST":
      codigo = request.form.get("codigo", "").strip()

      conexion = sqlite3.connect("acueducto_veredal.db")
      cursor = conexion.cursor()
      cursor.execute(
          "SELECT id, nombre_vecino, numero_documento, vereda FROM suscriptores"
          " WHERE numero_documento = ?",
          (codigo,),
      )
      suscriptor = cursor.fetchone()
      conexion.close()

      if not suscriptor:
        return f"<h3>Aviso: No se encontró ningún usuario con el código: {codigo}</h3><br><a href='/'>Volver a intentar</a>"

      return f"<h3>¡Conexión y búsqueda exitosa!</h3><p><b>Nombre:</b> {suscriptor[1]}</p><p><b>Vereda:</b> {suscriptor[3]}</p><br><a href='/'>Volver</a>"

    return render_template("index.html")

  except Exception as e:
    # Esto mostrará el error exacto en tu página web para saber qué está fallando
    return f"<h2 style='color:red;'>Error detallado de Python:</h2><pre>{traceback.format_exc()}</pre><br><a href='/'>Volver</a>"


if __name__ == "__main__":
  app.run(debug=True)
