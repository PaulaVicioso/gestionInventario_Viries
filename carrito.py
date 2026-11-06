from flask import render_template, Blueprint, redirect, url_for
from db import get_conexion
#Acá nostoros vamos a crear el BLUEPRINT
bp_carrito = Blueprint("carrito", __name__, url_prefix="/carrito")

MI_CARRITO = []

@bp_carrito.route("/")
def visualizarCarrito():
    conn = get_conexion()
    lista_productos = []
    for id in MI_CARRITO:
        producto = conn.execute("SELECT * FROM producto WHERE id_producto = ?", (id,) ).fetchone()
        lista_productos.append(producto)
    return render_template("carrito/ver_carrito.html", lista_productos=lista_productos)

@bp_carrito.route("/agregar/<int:id_producto>", methods=["POST"])
def agregar(id_producto):
    
    MI_CARRITO.append(id_producto)
    return redirect(url_for("productos.listaProductos"))