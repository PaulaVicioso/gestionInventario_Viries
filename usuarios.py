from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from db import get_conexion

bp_usuarios = Blueprint("usuarios", __name__, url_prefix="/usuarios")


ROLES_DEFAULT = [
    {"id": 1, "nombre": "Administrador"},
    {"id": 2, "nombre": "Cliente"},
]


@bp_usuarios.route("/nuevo", methods=["GET"])
def nuevo_usuario():
    return render_template("usuario-form.html", roles=ROLES_DEFAULT, usuario=None)

@bp_usuarios.route("/editar/<int:usuario_id>", methods=["GET"])
def editar_usuario(usuario_id):
    conn = get_conexion()
    usuario = conn.execute("SELECT * FROM usuario WHERE id = ?", (usuario_id,)).fetchone()
    conn.close()

    if not usuario:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("usuarios.nuevo_usuario"))

    return render_template("usuario-form.html", roles=ROLES_DEFAULT, usuario=usuario)

@bp_usuarios.route("/guardar", methods=["POST"])
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
            return redirect(url_for("usuarios.editar_usuario", usuario_id=int(usuario_id_raw)))
        return redirect(url_for("usuarios.nuevo_usuario"))

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
                return redirect(url_for("usuarios.nuevo_usuario"))

            password_final = generate_password_hash(password) if password else actual["password_hash"]
            cursor.execute("""
                UPDATE usuario
                SET nombre = ?, apellido = ?, password_hash = ?, rol_id = ?, medio = ?
                WHERE id = ?
            """, (nombre, apellido, password_final, rol_id, medio, uid))
            conn.commit()
            flash("Datos actualizados con éxito. El correo electrónico no fue modificado.", "success")
            return redirect(url_for("usuarios.editar_usuario", usuario_id=uid))

        else:
            if not email:
                flash("El email es obligatorio para registrar un usuario nuevo.", "warning")
                return redirect(url_for("usuarios.nuevo_usuario"))

            ya_existe = cursor.execute(
                "SELECT id FROM usuario WHERE LOWER(email) = LOWER(?)",
                (email,),
            ).fetchone()
            if ya_existe:
                flash("Ese email ya está registrado. Si querés editarlo, abrí ese usuario en modo edición.", "warning")
                return redirect(url_for("usuarios.editar_usuario", usuario_id=ya_existe["id"]))

            password_hash = generate_password_hash(password) if password else generate_password_hash("1234")
            cursor.execute("""
                INSERT INTO usuario (nombre, apellido, email, password_hash, rol_id, medio)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre, apellido, email, password_hash, rol_id, medio))
            conn.commit()
            nuevo_id = cursor.lastrowid
            flash("Registro completado con éxito.", "success")
            return redirect(url_for("usuarios.editar_usuario", usuario_id=nuevo_id))

    except Exception as e:
        conn.rollback()
        flash(f"Error al guardar el usuario: {e}", "danger")
        return redirect(url_for("usuarios.nuevo_usuario"))
    finally:
        conn.close()
