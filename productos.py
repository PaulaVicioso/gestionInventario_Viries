#datos con Jinja2? Revisar apuntes
#se pueden usar HTML de proyectos anteriores
# 26 de Noviembre
#CRUD Create Read Update Delete 
# Blueprint de alta de productos. Crear HTML de ellos. Completar los Trellos de ellos.
# Hardcorear el Rol de ADMIN
# El otro rol es de Cliente que es más limitado.

from flask import render_template, Blueprint, request, redirect, url_for
from db import get_conexion

bp_productos = Blueprint("productos", __name__, url_prefix="/productos")


@bp_productos.route("/")
def listaProductos():
    conn = get_conexion()
    
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT * FROM producto
                   """)
    
    productos = cursor.fetchall()
    conn.close()
    
    return render_template("productos/lista.html", productos = productos)

@bp_productos.route("/nuevo", methods=["GET", "POST"])
def crear():
    if request.method == "POST":
        nombre = request.form["nombre"]
        autor = request.form["autor"]
        tipo_articulo = request.form["tipo_articulo"]
        genero = request.form["genero"]
        idioma = request.form["idioma"]
        anio = int(request.form["anio"])
        precio = float(request.form["precio"])
        stock = int(request.form["stock"])

        conn = get_conexion()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO producto (nombre, autor, tipo_articulo, genero, idioma, anio, precio, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, autor, tipo_articulo, genero, idioma, anio, precio, stock))

        conn.commit()
        conn.close()

        return redirect(url_for("productos.listaProductos"))

    return render_template("productos/crear.html")

@bp_productos.route("/eliminar/<int:id_producto>", methods=["POST"])
def eliminar(id_producto):
    conn = get_conexion()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM producto WHERE id_producto = ?", (id_producto,))
    conn.commit()
    conn.close()

    return redirect(url_for("productos.listaProductos"))