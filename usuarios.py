from flask import Blueprint, abort, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash
from sqlalchemy import func, insert, literal, select
from sqlalchemy.exc import SQLAlchemyError

from db import Usuario, abrir_sesion

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

    with abrir_sesion() as datos:
        usuario = datos.get(Usuario, usuario_id)

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

    try:
        if usuario_id_raw:
            with abrir_sesion() as datos, datos.begin():
                actual = datos.get(Usuario, usuario_autenticado)
                if not actual:
                    flash("No se encontró el usuario a editar.", "danger")
                    return redirect(url_for("login"))

                actual.nombre = nombre
                actual.apellido = apellido
                actual.medio = medio
                if password:
                    actual.password_hash = generate_password_hash(password)

            session["usuario_nombre"] = nombre
            flash("Datos actualizados con éxito. El correo electrónico no fue modificado.", "success")
            return redirect(url_for(formulario))

        if not email:
            flash("El email es obligatorio para registrar un usuario nuevo.", "warning")
            return redirect(url_for(formulario))

        password_hash = generate_password_hash(password or "1234")
        # La búsqueda y el alta ocurren en una sola escritura para evitar duplicados concurrentes.
        existe = select(Usuario.id).where(func.lower(Usuario.email) == func.lower(email)).exists()
        nuevo = select(
            literal(nombre), literal(apellido), literal(email), literal(password_hash),
            literal(ROL_CLIENTE), literal(medio),
        ).where(~existe)
        alta = insert(Usuario.__table__).from_select(
            ["nombre", "apellido", "email", "password_hash", "rol_id", "medio"], nuevo
        )
        with abrir_sesion() as datos, datos.begin():
            creado = datos.execute(alta).rowcount == 1
        if not creado:
            flash("Ese email ya está registrado.", "warning")
            return redirect(url_for(formulario))

        flash("Registro completado con éxito.", "success")
        return redirect(url_for("login"))

    except SQLAlchemyError:
        flash("Error al guardar el usuario. Intentá de nuevo.", "danger")
        return redirect(url_for(formulario))
