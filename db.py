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
               INSERT INTO producto (nombre, autor, tipo_articulo, genero, idioma, anio, precio, stock)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               """, ("Harry Potter", "JK Rowling", "Libro", "Fantasía juvenil", "Inglés", 1997, 53500.00, 7))

    conn.commit()
    conn.close()

    if __name__ == "__main__":
        create_tables()