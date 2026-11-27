import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from productos import bp_productos
from carrito import bp_carrito
from usuarios import bp_usuarios
from werkzeug.security import check_password_hash
from db import abrir_sesion, buscar_usuario_por_email, init_db

app = Flask(__name__)
app.config["DATABASE_PATH"] = os.environ.get("VIRIES_DB_PATH") or os.path.join(app.root_path, "libreria.db")
app.config["VIRIES_ADMIN_EMAIL"] = os.environ.get("VIRIES_ADMIN_EMAIL", "")
app.config["VIRIES_ADMIN_PASSWORD"] = os.environ.get("VIRIES_ADMIN_PASSWORD", "")
app.secret_key = os.environ.get("SECRET_KEY", "dev-libreria-cambiar")

app.register_blueprint(bp_productos)
app.register_blueprint(bp_carrito)
app.register_blueprint(bp_usuarios)

init_db(app)

#Chicos, crear carpetas más tarde \(°A°)/
# y copiar los HTML de Librería de la materia Programación Avanzada → Hecho. Oh yeah
# CRUD Create Read Update Delete → coso para recordar

@app.route("/")
def index():
    return render_template("home.html")


@app.errorhandler(404)
def pagina_noexiste(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def error_interno(error):
    return render_template("500.html"), 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        with abrir_sesion() as datos:
            usuario = buscar_usuario_por_email(datos, email)

        if usuario and check_password_hash(usuario.password_hash, password):
            session["usuario_id"] = usuario.id
            session["usuario_nombre"] = usuario.nombre
            session["rol_id"] = usuario.rol_id
            flash(f"¡Bienvenido, {usuario.nombre}!", "success")
            return redirect(url_for("productos.listaProductos"))
        else:
            flash("Email o contraseña incorrectos.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)

''' GUARDADO POR LAS DUDAS AAAAA (°A°)
@app.route('/usuarios/nuevo')
def nuevo_usuario():
    roles = [{'id': 1, 'nombre': 'Administrador'}, {'id': 2, 'nombre': 'Cliente'}]
    return render_template('usuario-form.html', roles=roles)'''

if __name__ == "__main__":
    app.run(debug=True)

# . . .