#datos con Jinja2? Revisar apuntes
#se pueden usar HTML de proyectos anteriores
# 26 de Noviembre
#CRUD Create Read Update Delete 
# Blueprint de alta de productos. Crear HTML de ellos. Completar los Trellos de ellos.
# Hardcorear el Rol de ADMIN
# El otro rol es de Cliente que es más limitado.

from flask import abort, render_template, Blueprint, request, redirect, url_for, flash, session
from db import get_conexion

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

    datos = (
        nombre,
        autor,
        tipo_articulo,
        genero,
        idioma,
        anio,
        precio,
        stock,
        edad_minima,
        edad_maxima,
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

    condiciones = []
    parametros = []
    if edad is not None or genero:
        tipo_filtro = "Libro"
        categoria_param = "lectura"
    if tipo_filtro:
        condiciones.append("tipo_articulo = ?")
        parametros.append(tipo_filtro)
    if genero:
        condiciones.append("genero = ?")
        parametros.append(genero)
    if edad is not None:
        condiciones.extend((
            "(edad_minima IS NOT NULL OR edad_maxima IS NOT NULL)",
            "(edad_minima IS NULL OR edad_minima <= ?)",
            "(edad_maxima IS NULL OR edad_maxima >= ?)",
        ))
        parametros.extend((edad, edad))

    consulta = "SELECT * FROM producto"
    if condiciones:
        consulta += " WHERE " + " AND ".join(condiciones)

    conn = get_conexion()
    productos = conn.execute(consulta, parametros).fetchall()
    generos = conn.execute(
        "SELECT DISTINCT genero FROM producto WHERE tipo_articulo = 'Libro' ORDER BY genero COLLATE NOCASE"
    ).fetchall()
    conn.close()

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

    conn = get_conexion()
    try:
        with conn:
            resultado = conn.execute("""
                INSERT INTO reserva (usuario_id, id_producto)
                SELECT u.id, p.id_producto
                FROM usuario u CROSS JOIN producto p
                WHERE u.id = ? AND p.id_producto = ?
                    AND p.tipo_articulo = 'Libro' AND p.stock = 0
                ON CONFLICT(usuario_id, id_producto) DO NOTHING
            """, (usuario_id, id_producto))
            reservada = resultado.rowcount == 1
            existente = conn.execute(
                "SELECT 1 FROM reserva WHERE usuario_id = ? AND id_producto = ?",
                (usuario_id, id_producto),
            ).fetchone()
    finally:
        conn.close()

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

    conn = get_conexion()
    try:
        reservas = conn.execute("""
            SELECT p.nombre AS libro, r.id_producto, r.fecha_creacion
            FROM reserva r
            JOIN producto p ON p.id_producto = r.id_producto
            WHERE r.usuario_id = ?
            ORDER BY r.fecha_creacion, r.rowid
        """, (usuario_id,)).fetchall()
    finally:
        conn.close()
    return render_template("productos/reservas.html", reservas=reservas, administracion=False)


@bp_productos.route("/mis-reservas/<int:id_producto>/cancelar", methods=["POST"])
def cancelar_reserva(id_producto):
    usuario_id = session.get("usuario_id")
    if usuario_id is None:
        return redirect(url_for("login"))

    conn = get_conexion()
    try:
        with conn:
            canceladas = conn.execute("""
                DELETE FROM reserva WHERE usuario_id = ? AND id_producto = ?
            """, (usuario_id, id_producto)).rowcount
    finally:
        conn.close()

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

    conn = get_conexion()
    try:
        reservas = conn.execute("""
            SELECT p.nombre AS libro, u.nombre, u.apellido, u.email, r.fecha_creacion,
                   COUNT(*) OVER (PARTITION BY r.id_producto) AS pendientes
            FROM reserva r
            JOIN producto p ON p.id_producto = r.id_producto
            JOIN usuario u ON u.id = r.usuario_id
            ORDER BY r.fecha_creacion, r.rowid
        """).fetchall()
    finally:
        conn.close()
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

        conn = get_conexion()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO producto
            (nombre, autor, tipo_articulo, genero, idioma, anio, precio, stock, edad_minima, edad_maxima)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, datos)

        conn.commit()
        conn.close()

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

    conn = get_conexion()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM producto WHERE id_producto = ?",
        (id_producto,)
    )

    producto = cursor.fetchone()

    if producto is None:
        conn.close()
        flash("El producto que intentás editar no existe.", "danger")
        return redirect(url_for("productos.listaProductos"))

    if request.method == "POST":

        datos, error = validar_producto(request.form)

        if error:
            conn.close()
            flash(error, "danger")
            return render_template(
                "productos/editar.html",
                producto=producto
            ), 400

        cursor.execute("""
            UPDATE producto
            SET nombre = ?,
                autor = ?,
                tipo_articulo = ?,
                genero = ?,
                idioma = ?,
                anio = ?,
                precio = ?,
                stock = ?,
                edad_minima = ?,
                edad_maxima = ?
            WHERE id_producto = ?
        """, datos + (id_producto,))

        conn.commit()
        conn.close()

        flash("Producto modificado correctamente.", "success")
        return redirect(url_for("productos.listaProductos"))

    conn.close()

    return render_template(
        "productos/editar.html",
        producto=producto
    )

@bp_productos.route("/eliminar/<int:id_producto>", methods=["POST"])
def eliminar(id_producto):

    if not es_administrador():
        flash(
            "Acceso denegado: solo el Administrador puede dar de baja productos.",
            "danger"
        )
        return redirect(url_for("productos.listaProductos"))

    conn = get_conexion()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reserva WHERE id_producto = ?", (id_producto,))
    cursor.execute(
        "DELETE FROM producto WHERE id_producto = ?",
        (id_producto,)
    )

    eliminado = cursor.rowcount

    conn.commit()
    conn.close()

    if eliminado:
        flash("Producto dado de baja correctamente.", "success")
    else:
        flash("No se encontró el producto que intentabas eliminar.", "warning")

    return redirect(url_for("productos.listaProductos"))