# el profe dijo que puede haber un LogIn
# En las primeras clases habíamos visto condiciones para ser usuario o iniciar sesión
# Podemos usar APIS ajenas de otros lados. Pero no reemplazar contenido que vimos nosotros en clase.
# No usar SQL myAdmin

from pathlib import Path

from flask import current_app
from sqlalchemy import Float, ForeignKey, Integer, Text, URL, create_engine, func, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


'''NOmbre de del libro y del autor.
Tipo es uno de estos 3 artículos: Libro, Música y Película.
Ejemplos de Género: fantasía (libro), rock (música), thriller (película).
iDIOMA en que está el artículo: inglés, español, coreano, etc...
Año en el que salió el artículo. Evitar la Ñ.
Precio en pesos
Stock la cantidad'''

class Producto(Base):
    __tablename__ = "producto"
    __table_args__ = {"sqlite_autoincrement": True}

    id_producto: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(Text)
    autor: Mapped[str] = mapped_column(Text)
    tipo_articulo: Mapped[str] = mapped_column(Text)
    genero: Mapped[str] = mapped_column(Text)
    idioma: Mapped[str] = mapped_column(Text)
    anio: Mapped[int]
    precio: Mapped[float] = mapped_column(Float)
    stock: Mapped[int]
    edad_minima: Mapped[int | None]
    edad_maxima: Mapped[int | None]


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(Text)
    apellido: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    rol_id: Mapped[int]
    medio: Mapped[str] = mapped_column(Text)


class Compra(Base):
    __tablename__ = "compra"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    id_producto: Mapped[int] = mapped_column(ForeignKey("producto.id_producto"))
    cantidad: Mapped[int] = mapped_column(Integer, server_default=text("1"))
    total: Mapped[float] = mapped_column(Float)
    estado: Mapped[str] = mapped_column(Text, server_default="CONFIRMADA")
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"))


class Reserva(Base):
    __tablename__ = "reserva"

    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), primary_key=True)
    id_producto: Mapped[int] = mapped_column(ForeignKey("producto.id_producto"), primary_key=True)
    fecha_creacion: Mapped[str] = mapped_column(Text, server_default=func.current_timestamp())


def init_db(app):
    ruta = Path(app.config["DATABASE_PATH"]).expanduser().resolve()
    engine = create_engine(URL.create("sqlite", database=str(ruta)))
    app.extensions["viries_db"] = sessionmaker(engine, expire_on_commit=False)

    with engine.begin() as conexion:
        # Serializa el arranque si dos procesos inicializan la misma base.
        conexion.exec_driver_sql("BEGIN IMMEDIATE")
        Base.metadata.create_all(conexion)
        inspector = inspect(conexion)
        columnas_compra = {columna["name"] for columna in inspector.get_columns("compra")}
        if "usuario_id" not in columnas_compra:
            conexion.exec_driver_sql("ALTER TABLE compra ADD COLUMN usuario_id INTEGER REFERENCES usuario(id)")
        columnas_producto = {columna["name"] for columna in inspector.get_columns("producto")}
        for columna in ("edad_minima", "edad_maxima"):
            if columna not in columnas_producto:
                conexion.exec_driver_sql(f"ALTER TABLE producto ADD COLUMN {columna} INTEGER")

        with Session(conexion) as datos:
            if datos.scalar(select(Producto.id_producto).limit(1)) is None:
                datos.add(Producto(
                    nombre="Harry Potter", autor="JK Rowling", tipo_articulo="Libro",
                    genero="Fantasía juvenil", idioma="Inglés", anio=1997, precio=53500.00, stock=7,
                ))
                datos.flush()


def abrir_sesion():
    return current_app.extensions["viries_db"]()


def buscar_usuario_por_email(datos, email):
    return datos.scalar(select(Usuario).where(func.lower(Usuario.email) == func.lower(email)))
