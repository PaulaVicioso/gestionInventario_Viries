from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from db import get_conexion

bp_usuarios = Blueprint("usuarios", __name__, url_prefix="/usuarios")


ROL_CLIENTE = 2


@bp_usuarios.route("/nuevo", methods=["GET"])
def nuevo_usuario():
    return render_template("usuario-form.html", usuario=None)

@bp_usuarios.route("/perfil", methods=["GET"])
def mi_perfil():
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        return redirect(url_for("login"))
    return editar_usuario(usuario_id)


@bp_usuarios.route("/editar/<int:usuario_id>", methods=["GET"])
def editar_usuario(usuario_id):
    usuario_autenticado = session.get("usuario_id")
    if usuario_autenticado is None:
        return redirect(url_for("login"))
    if usuario_id != usuario_autenticado:
        abort(403)

    conn = get_conexion()
    usuario = conn.execute("SELECT * FROM usuario WHERE id = ?", (usuario_id,)).fetchone()
    conn.close()

    if not usuario:
        flash("Usuario no encontrado.", "danger")
        return redirect(url_for("login"))

    return render_template("usuario-form.html", usuario=usuario)

@bp_usuarios.route("/guardar", methods=["POST"])
def guardar_usuario():
    usuario_id_raw = request.form.get("id", "").strip()
    usuario_autenticado = session.get("usuario_id")
    if usuario_id_raw:
        if usuario_autenticado is None:
            return redirect(url_for("login"))
        if usuario_id_raw != str(usuario_autenticado):
            abort(403)

    formulario = "usuarios.mi_perfil" if usuario_id_raw else "usuarios.nuevo_usuario"
    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    medio = request.form.get("medio", "").strip()

    if not nombre or not apellido or not medio:
        flash("Nombre, apellido y medio de pago son obligatorios.", "warning")
        return redirect(url_for(formulario))

    conn = get_conexion()
    cursor = conn.cursor()

    try:
        if usuario_id_raw:
            uid = usuario_autenticado
            actual = cursor.execute("SELECT * FROM usuario WHERE id = ?", (uid,)).fetchone()
            if not actual:
                flash("No se encontró el usuario a editar.", "danger")
                return redirect(url_for("login"))

            password_final = generate_password_hash(password) if password else actual["password_hash"]
            cursor.execute("""
                UPDATE usuario
                SET nombre = ?, apellido = ?, password_hash = ?, medio = ?
                WHERE id = ?
            """, (nombre, apellido, password_final, medio, uid))
            conn.commit()
            session["usuario_nombre"] = nombre
            flash("Datos actualizados con éxito. El correo electrónico no fue modificado.", "success")
            return redirect(url_for(formulario))

        else:
            if not email:
                flash("El email es obligatorio para registrar un usuario nuevo.", "warning")
                return redirect(url_for("usuarios.nuevo_usuario"))

            ya_existe = cursor.execute(
                "SELECT id FROM usuario WHERE LOWER(email) = LOWER(?)",
                (email,),
            ).fetchone()
            if ya_existe:
                flash("Ese email ya está registrado.", "warning")
                return redirect(url_for("usuarios.nuevo_usuario"))

            password_hash = generate_password_hash(password) if password else generate_password_hash("1234")
            cursor.execute("""
                INSERT INTO usuario (nombre, apellido, email, password_hash, rol_id, medio)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre, apellido, email, password_hash, ROL_CLIENTE, medio))
            conn.commit()
            flash("Registro completado con éxito.", "success")
            return redirect(url_for("login"))

    except Exception as e:
        conn.rollback()
        flash(f"Error al guardar el usuario: {e}", "danger")
        return redirect(url_for(formulario))
    finally:
        conn.close()
