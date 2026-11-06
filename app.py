from flask import Flask, render_template, request, redirect, url_for, flash
from productos import bp_productos
from carrito import bp_carrito
from werkzeug.security import generate_password_hash
from db import create_tables

app = Flask(__name__)

app.register_blueprint(bp_productos)
app.register_blueprint(bp_carrito)

with app.app_context():
    create_tables()

#Chicos, crear carpetas más tarde \(°A°)/
# y copiar los HTML de Librería de la materia Programación Avanzada → Hecho. Oh yeah
# CRUD Create Read Update Delete → coso para recordar
@app.route("/")
def index():
    return render_template("index.html")

@app.errorhandler(404)
def pagina_noexiste(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def error_interno(error):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True)

@app.route('/usuarios/nuevo')
def nuevo_usuario():
    roles = [{'id': 1, 'nombre': 'Administrador'}, {'id': 2, 'nombre': 'Cliente'}]
    return render_template('usuario-form.html', roles=roles)
# . . .