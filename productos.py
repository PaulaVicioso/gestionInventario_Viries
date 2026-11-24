#datos con Jinja2? Revisar apuntes
#se pueden usar HTML de proyectos anteriores
# 26 de Noviembre
#CRUD Create Read Update Delete 
# Blueprint de alta de productos. Crear HTML de ellos. Completar los Trellos de ellos.
# Hardcorear el Rol de ADMIN
# El otro rol es de Cliente que es más limitado.

from flask import render_template, Blueprint, request, redirect, url_for, flash, session
from db import get_conexion

TIPOS_ARTICULO = ("Libro", "Música", "Película")

bp_productos = Blueprint("productos", __name__, url_prefix="/productos")

MAPEO_CATEGORIAS = {
    "lectura": "Libro",
    "libro": "Libro",
    "musica": "Música",
    "música": "Música",
    "video": "Película",
    "pelicula": "Película",
    "película": "Película",
}


@bp_productos.route("/")
def listaProductos():
    categoria_param = request.args.get("categoria", "").strip().lower()
    tipo_filtro = MAPEO_CATEGORIAS.get(categoria_param)

    conn = get_conexion()
    cursor = conn.cursor()

    if tipo_filtro:
        cursor.execute("SELECT * FROM producto WHERE LOWER(tipo_articulo) = LOWER(?)", (tipo_filtro,))
    else:
        cursor.execute("SELECT * FROM producto")

    productos = cursor.fetchall()
    conn.close()

    return render_template(
        "productos/lista.html",
        productos=productos,
        categoria_actual=categoria_param,
    )

@bp_productos.route("/nuevo", methods=["GET", "POST"])
def crear():
    if session.get("rol_id") != 1:
        flash("Acceso denegado: solo el Administrador puede dar de alta o baja productos.", "danger")
        return redirect(url_for("productos.listaProductos"))

    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        autor = request.form["autor"].strip()
        tipo_articulo = request.form["tipo_articulo"]
        genero = request.form["genero"].strip()
        idioma = request.form["idioma"].strip()

        try:
            anio = int(request.form["anio"])
            precio = float(request.form["precio"])
            stock = int(request.form["stock"])
        except ValueError:
            flash("Año, precio y stock deben ser números válidos")
            return render_template("productos/crear.html"), 400

        if not all([nombre, autor, genero, idioma]):
            flash("Todos los campos son obligatorios")
            return render_template("productos/crear.html"), 400
        if tipo_articulo not in TIPOS_ARTICULO:
            flash("Tipo de artículo inválido")
            return render_template("productos/crear.html"), 400
        if precio < 0 or stock < 0:
            flash("El precio y el stock no pueden ser negativos")
            return render_template("productos/crear.html"), 400

        conn = get_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO producto (nombre, autor, tipo_articulo, genero, idioma, anio, precio, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, autor, tipo_articulo, genero, idioma, anio, precio, stock))

        conn.commit()
        conn.close()

        flash("Producto registrado correctamente")
        return redirect(url_for("productos.listaProductos"))
    return render_template("productos/crear.html")

@bp_productos.route("/eliminar/<int:id_producto>", methods=["POST"])
def eliminar(id_producto):
    if session.get("rol_id") != 1:
        flash("Acceso denegado: solo el Administrador puede dar de alta o baja productos.", "danger")
        return redirect(url_for("productos.listaProductos"))

    conn = get_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM producto WHERE id_producto = ?", (id_producto,))
    conn.commit()
    conn.close()

    return redirect(url_for("productos.listaProductos"))