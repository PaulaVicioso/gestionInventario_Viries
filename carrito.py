from flask import render_template, Blueprint, redirect, url_for, flash, request, session
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
    lista_productos = []
    for prod_id in MI_CARRITO:
        producto = conn.execute("SELECT * FROM producto WHERE id_producto = ?", (prod_id,)).fetchone()
        if producto:
            lista_productos.append(producto)
    compras = conn.execute("""
        SELECT c.id, c.cantidad, c.total, c.estado, p.nombre AS titulo
        FROM compra c
        JOIN producto p ON p.id_producto = c.id_producto
        ORDER BY c.id DESC
    """).fetchall()
    conn.close()
    return render_template("compra-lista.html", lista_productos=lista_productos, compras=compras)

@bp_carrito.route("/agregar/<int:id_producto>", methods=["POST"])
def agregar(id_producto):
    MI_CARRITO.append(id_producto)
    flash("Artículo agregado al carrito.", "info")
    return redirect(url_for("productos.listaProductos"))

@bp_carrito.route("/comprar/<int:id_producto>", methods=["POST"])
def comprar_ahora(id_producto):
    conn = get_conexion()
    cursor = conn.cursor()
    producto = cursor.execute("SELECT * FROM producto WHERE id_producto = ?", (id_producto,)).fetchone()

    if not producto:
        conn.close()
        flash("El artículo seleccionado no existe.", "danger")
        return redirect(url_for("productos.listaProductos"))

    if producto["stock"] <= 0:
        conn.close()
        flash("No hay stock disponible para este artículo.", "warning")
        return redirect(url_for("productos.listaProductos"))

    nuevo_stock = producto["stock"] - 1
    cursor.execute("UPDATE producto SET stock = ? WHERE id_producto = ?", (nuevo_stock, id_producto))
    cursor.execute("""
        INSERT INTO compra (id_producto, cantidad, total, estado)
        VALUES (?, ?, ?, ?)
    """, (id_producto, 1, producto["precio"], "CONFIRMADA"))
    conn.commit()
    conn.close()

    flash(f"¡Compra exitosa! Adquiriste '{producto['nombre']}'.", "success")
    return redirect(url_for("carrito.visualizarCarrito"))