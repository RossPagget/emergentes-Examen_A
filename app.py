import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
DATABASE = "inventario.db"


# ── Base de datos ────────────────────────────────────────
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT    NOT NULL,
            categoria TEXT    NOT NULL,
            precio    REAL    NOT NULL,
            stock     INTEGER NOT NULL
        )
    """)
    # Datos de ejemplo si la tabla está vacía
    if db.execute("SELECT COUNT(*) FROM productos").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO productos (nombre, categoria, precio, stock) VALUES (?,?,?,?)",
            [
                ("Teclado Mecánico",  "Periféricos",  85.00,  15),
                ("Mouse Inalámbrico", "Periféricos",  35.00,  30),
                ("Monitor 24\"",      "Pantallas",   220.00,   8),
                ("Auriculares USB",   "Audio",        55.00,  20),
                ("Webcam HD",         "Periféricos",  70.00,  12),
                ("Hub USB-C",         "Accesorios",   28.00,  25),
                ("Laptop Gamer",      "Computadoras",1200.00,  5),
                ("SSD 1TB",           "Almacenamiento",95.00, 18),
            ]
        )
        db.commit()
    db.close()


# ── Rutas ────────────────────────────────────────────────

# Listar
@app.route("/")
def index():
    db    = get_db()
    busca = request.args.get("q", "").strip()
    if busca:
        productos = db.execute(
            "SELECT * FROM productos WHERE nombre LIKE ? OR categoria LIKE ? ORDER BY id",
            (f"%{busca}%", f"%{busca}%")
        ).fetchall()
    else:
        productos = db.execute("SELECT * FROM productos ORDER BY id").fetchall()
    total_items  = db.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    total_valor  = db.execute("SELECT SUM(precio * stock) FROM productos").fetchone()[0] or 0
    return render_template("index.html",
                           productos=productos,
                           total_items=total_items,
                           total_valor=total_valor,
                           busca=busca)


# Registrar — GET muestra form, POST guarda
@app.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    error = None
    form  = {}
    if request.method == "POST":
        form = request.form
        nombre    = form.get("nombre",    "").strip()
        categoria = form.get("categoria", "").strip()
        try:
            precio = float(form.get("precio", ""))
            stock  = int(form.get("stock",  ""))
            if not nombre or not categoria:
                raise ValueError("Campos vacíos")
            if precio < 0 or stock < 0:
                raise ValueError("Valores negativos")
        except ValueError:
            error = "Todos los campos son obligatorios y deben tener valores válidos."
        else:
            get_db().execute(
                "INSERT INTO productos (nombre, categoria, precio, stock) VALUES (?,?,?,?)",
                (nombre, categoria, precio, stock)
            )
            get_db().commit()
            return redirect(url_for("index"))
    return render_template("formulario.html", accion="Nuevo", producto=form, error=error)


# Editar — GET carga datos, POST actualiza
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    db      = get_db()
    producto = db.execute("SELECT * FROM productos WHERE id=?", (id,)).fetchone()
    if not producto:
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        nombre    = request.form.get("nombre",    "").strip()
        categoria = request.form.get("categoria", "").strip()
        try:
            precio = float(request.form.get("precio", ""))
            stock  = int(request.form.get("stock",  ""))
            if not nombre or not categoria:
                raise ValueError
            if precio < 0 or stock < 0:
                raise ValueError
        except ValueError:
            error = "Todos los campos son obligatorios y deben tener valores válidos."
        else:
            db.execute(
                "UPDATE productos SET nombre=?, categoria=?, precio=?, stock=? WHERE id=?",
                (nombre, categoria, precio, stock, id)
            )
            db.commit()
            return redirect(url_for("index"))
    return render_template("formulario.html", accion="Editar", producto=producto, error=error)


# Eliminar
@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    db = get_db()
    db.execute("DELETE FROM productos WHERE id=?", (id,))
    db.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
