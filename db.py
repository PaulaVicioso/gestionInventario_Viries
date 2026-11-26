# el profe dijo que puede haber un LogIn
# En las primeras clases habíamos visto condiciones para ser usuario o iniciar sesión
# Podemos usar APIS ajenas de otros lados. Pero no reemplazar contenido que vimos nosotros en clase.
# No usar SQL myAdmin

import sqlite3

def get_conexion():
    conn = sqlite3.connect("libreria.db")    
    conn.row_factory = sqlite3.Row    
    return conn

'''NOmbre de del libro y del autor.
Tipo es uno de estos 3 artículos: Libro, Música y Película.
Ejemplos de Género: fantasía (libro), rock (música), thriller (película).
iDIOMA en que está el artículo: inglés, español, coreano, etc...
Año en el que salió el artículo. Evitar la Ñ.
Precio en pesos
Stock la cantidad'''

def create_tables():
    conn = get_conexion()
    cursor = conn.cursor()
    cursor.execute("BEGIN IMMEDIATE")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS producto (
            id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            autor TEXT NOT NULL,
            tipo_articulo TEXT NOT NULL,
            genero TEXT NOT NULL,
            idioma TEXT NOT NULL,
            anio INTEGER NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            rol_id INTEGER NOT NULL,
            medio TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_producto INTEGER NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 1,
            total REAL NOT NULL,
            estado TEXT NOT NULL DEFAULT 'CONFIRMADA',
            FOREIGN KEY (id_producto) REFERENCES producto (id_producto)
        )
    """)

    columnas_producto = {columna["name"] for columna in cursor.execute("PRAGMA table_info(producto)")}
    for columna in ("edad_minima", "edad_maxima"):
        if columna not in columnas_producto:
            cursor.execute(f"ALTER TABLE producto ADD COLUMN {columna} INTEGER")

    existente = cursor.execute("SELECT COUNT(*) AS total FROM producto").fetchone()
    if existente["total"] == 0:
        cursor.execute("""
            INSERT INTO producto (nombre, autor, tipo_articulo, genero, idioma, anio, precio, stock)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, ("Harry Potter", "JK Rowling", "Libro", "Fantasía juvenil", "Inglés", 1997, 53500.00, 7))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()