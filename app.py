#PARA MODIFICAR

from flask import Flask, render_template, redirect, url_for
from productos import bp_productos
from carrito import bp_carrito
from db import create_tables


app = Flask(__name__)

app.register_blueprint(bp_productos)
app.register_blueprint(bp_carrito)


with app.app_context():
    create_tables()


@app.route("/")
def index():
    return render_template("index.html") #Me devuelve a la pagina principal


@app.errorhandler(404)
def pagina_noexiste(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def error_interno(error):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True)

# . . .