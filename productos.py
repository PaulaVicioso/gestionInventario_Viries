#datos con Jinja2? Revisar apuntes
#se pueden usar HTML de proyectos anteriores
# 26 de Noviembre
#CRUD Create Read Update Delete 
# Blueprint de alta de productos. Crear HTML de ellos. Completar los Trellos de ellos.
# Hardcorear el Rol de ADMIN
# El otro rol es de Cliente que es más limitado.

from flask import abort, render_template, Blueprint, request, redirect, url_for, flash, session
from sqlalchemy import delete, func, literal_column, or_, select
from sqlalchemy.dialects.sqlite import insert

from db import Producto, Reserva, Usuario, abrir_sesion

TIPOS_ARTICULO = ("Libro", "Música", "Película")

bp_productos = Blueprint("productos", __name__, url_prefix="/productos")

# Luego tenemos que unificar cómo llamarlos. 
# ¿O lo dejamos así por si el potencial Usuario llega a escribir mal?
# Nah creo que va a ser muy redundante. ¿Qué dicen?
MAPEO_CATEGORIAS = {
    "lectura": "Libro",
    "libro": "Libro",
    "musica": "Música",
    "música": "Música",
    "video": "Película",
    "pelicula": "Película",
    "película": "Película",
}

def es_administrador():
    return session.get("rol_id") == 1

def edad_opcional(valor):
    if not valor.strip():
        return None
    edad = int(valor)
    if not 0 <= edad <= 2**63 - 1:
        raise ValueError("Edad fuera de rango")
    return edad


def validar_producto(formulario):

    nombre = formulario.get("nombre", "").strip()
    autor = formulario.get("autor", "").strip()
    tipo_articulo = formulario.get("tipo_articulo", "").strip()
    genero = formulario.get("genero", "").strip()
    idioma = formulario.get("idioma", "").strip()

    if not all([nombre, autor, tipo_articulo, genero, idioma]):
        return None, "Todos los campos son obligatorios."

    if tipo_articulo not in TIPOS_ARTICULO:
        return None, "El tipo de artículo seleccionado no es válido."

    try:
        anio = int(formulario.get("anio", ""))
        precio = float(formulario.get("precio", ""))
        stock = int(formulario.get("stock", ""))
    except (ValueError, TypeError):
        return None, "Año, precio y stock deben ser números válidos."

    if anio <= 0:
        return None, "El año debe ser mayor que cero."

    if precio < 0:
        return None, "El precio no puede ser negativo."

    if stock < 0:
        return None, "El stock no puede ser negativo."

    edad_minima = edad_maxima = None
    try:
        if tipo_articulo in ("Libro", "Película"):
            edad_minima = edad_opcional(formulario.get("edad_minima", ""))
        if tipo_articulo == "Libro":
            edad_maxima = edad_opcional(formulario.get("edad_maxima", ""))
    except ValueError:
        return None, "Las edades deben ser enteras y no negativas."

    if edad_minima is not None and edad_maxima is not None and edad_minima > edad_maxima:
        return None, "La edad mínima no puede superar la máxima."

    datos = dict(
        nombre=nombre,
        autor=autor,
        tipo_articulo=tipo_articulo,
        genero=genero,
        idioma=idioma,
        anio=anio,
        precio=precio,
        stock=stock,
        edad_minima=edad_minima,
        edad_maxima=edad_maxima,
    )

    return datos, None


# LISTADO DE PRODUCTOS
@bp_productos.route("/")
def listaProductos():

    categoria_param = request.args.get("categoria", "").strip().lower()
    tipo_filtro = MAPEO_CATEGORIAS.get(categoria_param)

    edad_texto = request.args.get("edad", "").strip()
    genero = request.args.get("genero", "").strip()
    try:
        edad = edad_opcional(edad_texto)
    except ValueError:
        flash("Ingresá una edad entera y no negativa.", "warning")
        return redirect(url_for("productos.listaProductos", categoria=categoria_param, genero=genero))

    if edad is not None or genero:
        tipo_filtro = "Libro"
        categoria_param = "lectura"

    consulta = select(Producto).order_by(Producto.id_producto)
    if tipo_filtro:
        consulta = consulta.where(Producto.tipo_articulo == tipo_filtro)
    if genero:
        consulta = consulta.where(Producto.genero == genero)
    if edad is not None:
        consulta = consulta.where(
            or_(Producto.edad_minima.is_not(None), Producto.edad_maxima.is_not(None)),
            or_(Producto.edad_minima.is_(None), Producto.edad_minima <= edad),
            or_(Producto.edad_maxima.is_(None), Producto.edad_maxima >= edad),
        )

    with abrir_sesion() as datos:
        productos = datos.scalars(consulta).all()
        generos = datos.execute(
            select(Producto.genero).where(Producto.tipo_articulo == "Libro").distinct()
            .order_by(Producto.genero.collate("NOCASE"))
        ).all()

    return render_template(
        "productos/lista.html",
        productos=productos,
        categoria_actual=categoria_param,
        edad=edad_texto,
        genero=genero,
        generos=generos,
    )


@bp_productos.route("/reservar/<int:id_producto>", methods=["POST"])
def reservar(id_producto):
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        flash("Iniciá sesión para reservar un libro.", "warning")
        return redirect(url_for("login"))

    elegible = (
        select(Usuario.id, Producto.id_producto)
        .select_from(Usuario)
        .join(Producto, Producto.id_producto == id_producto)
        .where(Usuario.id == usuario_id, Producto.tipo_articulo == "Libro", Producto.stock == 0)
    )
    solicitud = (
        insert(Reserva).from_select(["usuario_id", "id_producto"], elegible)
        .on_conflict_do_nothing(index_elements=[Reserva.usuario_id, Reserva.id_producto])
    )
    with abrir_sesion() as datos, datos.begin():
        reservada = datos.execute(solicitud).rowcount == 1
        existente = reservada or datos.get(Reserva, (usuario_id, id_producto)) is not None

    if reservada:
        flash("Reserva confirmada.", "success")
    elif existente:
        flash("Ya tenés una reserva para este libro.", "info")
    else:
        flash("Solo se pueden reservar libros sin stock.", "warning")

    filtros = {clave: request.args[clave] for clave in ("categoria", "edad", "genero") if clave in request.args}
    return redirect(url_for("productos.listaProductos", **filtros))


@bp_productos.route("/mis-reservas")
def mis_reservas():
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        return redirect(url_for("login"))

    with abrir_sesion() as datos:
        reservas = datos.execute(
            select(Producto.nombre.label("libro"), Reserva.id_producto, Reserva.fecha_creacion)
            .join(Producto, Producto.id_producto == Reserva.id_producto)
            .where(Reserva.usuario_id == usuario_id)
            .order_by(Reserva.fecha_creacion, literal_column("reserva.rowid"))
        ).all()
    return render_template("productos/reservas.html", reservas=reservas, administracion=False)


@bp_productos.route("/mis-reservas/<int:id_producto>/cancelar", methods=["POST"])
def cancelar_reserva(id_producto):
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        return redirect(url_for("login"))

    with abrir_sesion() as datos, datos.begin():
        canceladas = datos.execute(
            delete(Reserva).where(Reserva.usuario_id == usuario_id, Reserva.id_producto == id_producto)
        ).rowcount

    if canceladas:
        flash("Reserva cancelada.", "success")
    else:
        flash("No tenés una reserva pendiente para ese libro.", "info")
    return redirect(url_for("productos.mis_reservas"))


@bp_productos.route("/reservas")
def listar_reservas():
    if session.get("usuario_id") is None:
        return redirect(url_for("login"))
    if not es_administrador():
        abort(403)

    with abrir_sesion() as datos:
        reservas = datos.execute(
            select(
                Producto.nombre.label("libro"), Usuario.nombre, Usuario.apellido,
                Usuario.email, Reserva.fecha_creacion,
                func.count().over(partition_by=Reserva.id_producto).label("pendientes"),
            )
            .select_from(Reserva)
            .join(Producto, Producto.id_producto == Reserva.id_producto)
            .join(Usuario, Usuario.id == Reserva.usuario_id)
            .order_by(Reserva.fecha_creacion, literal_column("reserva.rowid"))
        ).all()
    return render_template("productos/reservas.html", reservas=reservas, administracion=True)


# ALTA DE PRODUCTOS
@bp_productos.route("/nuevo", methods=["GET", "POST"])
def crear():

    if not es_administrador():
        flash(
            "Acceso denegado: solo el Administrador puede dar de alta productos.",
            "danger"
        )
        return redirect(url_for("productos.listaProductos"))

    if request.method == "POST":

        datos, error = validar_producto(request.form)

        if error:
            flash(error, "danger")
            return render_template("productos/crear.html"), 400

        with abrir_sesion() as db, db.begin():
            db.add(Producto(**datos))

        flash("Producto registrado correctamente.", "success")
        return redirect(url_for("productos.listaProductos"))

    return render_template("productos/crear.html")


# EDICIÓN DE PRODUCTOS
@bp_productos.route("/editar/<int:id_producto>", methods=["GET", "POST"])
def editar(id_producto):

    if not es_administrador():
        flash(
            "Acceso denegado: solo el Administrador puede modificar productos.",
            "danger"
        )
        return redirect(url_for("productos.listaProductos"))

    with abrir_sesion() as db, db.begin():
        producto = db.get(Producto, id_producto)
        if producto is None:
            flash("El producto que intentás editar no existe.", "danger")
            return redirect(url_for("productos.listaProductos"))

        if request.method == "POST":
            datos, error = validar_producto(request.form)
            if error:
                flash(error, "danger")
                return render_template("productos/editar.html", producto=producto), 400

            for campo, valor in datos.items():
                setattr(producto, campo, valor)

    if request.method == "POST":
        flash("Producto modificado correctamente.", "success")
        return redirect(url_for("productos.listaProductos"))
    return render_template("productos/editar.html", producto=producto)


@bp_productos.route("/eliminar/<int:id_producto>", methods=["POST"])
def eliminar(id_producto):

    if not es_administrador():
        flash(
            "Acceso denegado: solo el Administrador puede dar de baja productos.",
            "danger"
        )
        return redirect(url_for("productos.listaProductos"))

    with abrir_sesion() as db, db.begin():
        db.execute(delete(Reserva).where(Reserva.id_producto == id_producto))
        eliminado = db.execute(delete(Producto).where(Producto.id_producto == id_producto)).rowcount

    if eliminado:
        flash("Producto dado de baja correctamente.", "success")
    else:
        flash("No se encontró el producto que intentabas eliminar.", "warning")

    return redirect(url_for("productos.listaProductos"))