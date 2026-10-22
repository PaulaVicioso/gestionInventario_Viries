#PARA MODIFICAR

from flask import render_template, Blueprint
from db import get_conexion
#Acá nostoros vamos a crear el BLUEPRINT
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
    
    
    return render_template("productos/lista.html", productos = productos)#Me devuelve a la pagina de productos

#blueprint para agregar productos