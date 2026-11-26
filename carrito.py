from flask import abort, render_template, Blueprint, redirect, url_for, flash, request, session
from sqlalchemy import select, update

from db import Compra, Producto, Usuario, abrir_sesion
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
    consulta = (
        select(Compra.id, Compra.id_producto, Compra.cantidad, Compra.total,
               Compra.estado, Producto.nombre.label("titulo"))
        .outerjoin(Producto, Producto.id_producto == Compra.id_producto)
        .where(Compra.usuario_id == session["usuario_id"])
        .order_by(Compra.id.desc())
    )
    with abrir_sesion() as datos:
        compras = datos.execute(consulta).all()
    return render_template("compra-lista.html", compras=compras, ventas=False)


@bp_carrito.route("/ventas")
def listar_ventas():
    if session.get("rol_id") != 1:
        abort(403)

    consulta = (
        select(Compra.id, Compra.id_producto, Compra.cantidad, Compra.total, Compra.estado,
               Producto.nombre.label("titulo"), Usuario.nombre, Usuario.apellido, Usuario.email)
        .outerjoin(Producto, Producto.id_producto == Compra.id_producto)
        .outerjoin(Usuario, Usuario.id == Compra.usuario_id)
        .order_by(Compra.id.desc())
    )
    with abrir_sesion() as datos:
        compras = datos.execute(consulta).all()
    return render_template("compra-lista.html", compras=compras, ventas=True)


@bp_carrito.route("/agregar/<int:id_producto>", methods=["POST"])
def agregar(id_producto):
    MI_CARRITO.append(id_producto)
    flash("Artículo agregado al carrito.", "info")
    return redirect(url_for("productos.listaProductos"))

@bp_carrito.route("/comprar/<int:id_producto>", methods=["POST"])
def comprar_ahora(id_producto):
    with abrir_sesion() as datos, datos.begin():
        descontadas = datos.execute(
            update(Producto).where(Producto.id_producto == id_producto, Producto.stock > 0)
            .values(stock=Producto.stock - 1)
        ).rowcount
        producto = datos.get(Producto, id_producto)

        if producto is None:
            flash("El artículo seleccionado no existe.", "danger")
            return redirect(url_for("productos.listaProductos"))
        if not descontadas:
            flash("No hay stock disponible para este artículo.", "warning")
            return redirect(url_for("productos.listaProductos"))

        datos.add(Compra(
            id_producto=id_producto, cantidad=1, total=producto.precio,
            estado="CONFIRMADA", usuario_id=session["usuario_id"],
        ))

    flash(f"¡Compra exitosa! Adquiriste '{producto.nombre}'.", "success")
    return redirect(url_for("carrito.visualizarCarrito"))
