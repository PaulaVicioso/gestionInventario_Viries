from flask import abort, render_template, Blueprint, redirect, url_for, flash, request, session
from db import get_conexion
#Acá nostoros vamos a crear el BLUEPRINT
bp_carrito = Blueprint("carrito", __name__, url_prefix="/carrito")

MI_CARRITO = []


@bp_carrito.before_request
def requerir_sesion():
    if session.get("usuario_id") is None:
        if request.endpoint == "carrito.comprar_ahora":
            flash("Para comprar, primero iniciá sesión.", "warning")
        return redirect(url_for("login"))


@bp_carrito.route("/")
def visualizarCarrito():
    conn = get_conexion()
    try:
        compras = conn.execute("""
            SELECT c.id, c.id_producto, c.cantidad, c.total, c.estado, p.nombre AS titulo
            FROM compra c
            LEFT JOIN producto p ON p.id_producto = c.id_producto
            WHERE c.usuario_id = ?
            ORDER BY c.id DESC
        """, (session["usuario_id"],)).fetchall()
    finally:
        conn.close()
    return render_template("compra-lista.html", compras=compras, ventas=False)


@bp_carrito.route("/ventas")
def listar_ventas():
    if session.get("rol_id") != 1:
        abort(403)

    conn = get_conexion()
    try:
        compras = conn.execute("""
            SELECT c.id, c.id_producto, c.cantidad, c.total, c.estado, p.nombre AS titulo,
                   u.nombre, u.apellido, u.email
            FROM compra c
            LEFT JOIN producto p ON p.id_producto = c.id_producto
            LEFT JOIN usuario u ON u.id = c.usuario_id
            ORDER BY c.id DESC
        """).fetchall()
    finally:
        conn.close()
    return render_template("compra-lista.html", compras=compras, ventas=True)


@bp_carrito.route("/agregar/<int:id_producto>", methods=["POST"])
def agregar(id_producto):
    MI_CARRITO.append(id_producto)
    flash("Artículo agregado al carrito.", "info")
    return redirect(url_for("productos.listaProductos"))

@bp_carrito.route("/comprar/<int:id_producto>", methods=["POST"])
def comprar_ahora(id_producto):
    conn = get_conexion()
    try:
        with conn:
            conn.execute("BEGIN IMMEDIATE")
            producto = conn.execute(
                "SELECT * FROM producto WHERE id_producto = ?", (id_producto,)
            ).fetchone()

            if not producto:
                flash("El artículo seleccionado no existe.", "danger")
                return redirect(url_for("productos.listaProductos"))

            if producto["stock"] <= 0:
                flash("No hay stock disponible para este artículo.", "warning")
                return redirect(url_for("productos.listaProductos"))

            conn.execute(
                "UPDATE producto SET stock = stock - 1 WHERE id_producto = ?", (id_producto,)
            )
            conn.execute("""
                INSERT INTO compra (id_producto, cantidad, total, estado, usuario_id)
                VALUES (?, ?, ?, ?, ?)
            """, (id_producto, 1, producto["precio"], "CONFIRMADA", session["usuario_id"]))
    finally:
        conn.close()

    flash(f"¡Compra exitosa! Adquiriste '{producto['nombre']}'.", "success")
    return redirect(url_for("carrito.visualizarCarrito"))