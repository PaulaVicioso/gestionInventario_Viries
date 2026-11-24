import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from productos import bp_productos
from carrito import bp_carrito
from werkzeug.security import generate_password_hash, check_password_hash
from db import create_tables, get_conexion

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-libreria-cambiar")

app.register_blueprint(bp_productos)
app.register_blueprint(bp_carrito)

with app.app_context():
    create_tables()

#Chicos, crear carpetas más tarde \(°A°)/
# y copiar los HTML de Librería de la materia Programación Avanzada → Hecho. Oh yeah
# CRUD Create Read Update Delete → coso para recordar
ROLES_DEFAULT = [
    {"id": 1, "nombre": "Administrador"},
    {"id": 2, "nombre": "Cliente"},
]

@app.route("/")
def index():
    return render_template("home.html")


@app.route("/usuarios/nuevo", methods=["GET"])
def nuevo_usuario():
    return render_template("usuario-form.html", roles=ROLES_DEFAULT, usuario=None)

@app.route("/usuarios/editar/<int:usuario_id>", methods=["GET"])
def editar_usuario(usuario_id):
    conn = get_conexion()
    usuario = conn.execute("SELECT * FROM usuario WHERE id = ?", (usuario_id,)).fetchone()
    conn.close()

    if not usuario:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("nuevo_usuario"))

    return render_template("usuario-form.html", roles=ROLES_DEFAULT, usuario=usuario)

@app.route("/usuarios/guardar", methods=["POST"])
def guardar_usuario():
    usuario_id_raw = request.form.get("id", "").strip()
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    rol_id_raw = request.form.get("rol.id", "2").strip()
    medio = request.form.get("medio", "").strip()

    if not nombre or not apellido or not medio:
        flash("Nombre, apellido y medio de pago son obligatorios.", "warning")
        if usuario_id_raw.isdigit():
            return redirect(url_for("editar_usuario", usuario_id=int(usuario_id_raw)))
        return redirect(url_for("nuevo_usuario"))

    try:
        rol_id = int(rol_id_raw) if rol_id_raw else 2
    except ValueError:
        rol_id = 2

    conn = get_conexion()
    cursor = conn.cursor()

    try:
        if usuario_id_raw.isdigit():
            uid = int(usuario_id_raw)
            actual = cursor.execute("SELECT * FROM usuario WHERE id = ?", (uid,)).fetchone()
            if not actual:
                flash("No se encontró el usuario a editar.", "danger")
                return redirect(url_for("nuevo_usuario"))

            password_final = generate_password_hash(password) if password else actual["password_hash"]
            cursor.execute("""
                UPDATE usuario
                SET nombre = ?, apellido = ?, password_hash = ?, rol_id = ?, medio = ?
                WHERE id = ?
            """, (nombre, apellido, password_final, rol_id, medio, uid))
            conn.commit()
            flash("Datos actualizados con éxito. El correo electrónico no fue modificado.", "success")
            return redirect(url_for("editar_usuario", usuario_id=uid))

        else:
            if not email:
                flash("El email es obligatorio para registrar un usuario nuevo.", "warning")
                return redirect(url_for("nuevo_usuario"))

            ya_existe = cursor.execute(
                "SELECT id FROM usuario WHERE LOWER(email) = LOWER(?)",
                (email,),
            ).fetchone()
            if ya_existe:
                flash("Ese email ya está registrado. Si querés editarlo, abrí ese usuario en modo edición.", "warning")
                return redirect(url_for("editar_usuario", usuario_id=ya_existe["id"]))

            password_hash = generate_password_hash(password) if password else generate_password_hash("1234")
            cursor.execute("""
                INSERT INTO usuario (nombre, apellido, email, password_hash, rol_id, medio)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre, apellido, email, password_hash, rol_id, medio))
            conn.commit()
            nuevo_id = cursor.lastrowid
            flash("Registro completado con éxito.", "success")
            return redirect(url_for("editar_usuario", usuario_id=nuevo_id))

    except Exception as e:
        conn.rollback()
        flash(f"Error al guardar el usuario: {e}", "danger")
        return redirect(url_for("nuevo_usuario"))
    finally:
        conn.close()


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

        conn = get_conexion()
        usuario = conn.execute(
            "SELECT * FROM usuario WHERE LOWER(email) = LOWER(?)",
            (email,),
        ).fetchone()
        conn.close()

        if usuario and check_password_hash(usuario["password_hash"], password):
            session["usuario_id"] = usuario["id"]
            session["usuario_nombre"] = usuario["nombre"]
            session["rol_id"] = usuario["rol_id"]
            flash(f"¡Bienvenido, {usuario['nombre']}!", "success")
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