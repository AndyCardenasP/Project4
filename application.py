# Author: Andrés Fernando Cárdenas Ponce
# This is the application.py file
# <!--Proyect4 | WebProgramming Python and JavaScript-->
from flask import Flask, session, render_template, request, jsonify, redirect, url_for
from flask_bootstrap import Bootstrap
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
import requests
import os

app = Flask(__name__)

# Check for environment variable
# if not os.getenv("DATABASE_URL"):
#    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)
Bootstrap(app)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

tipos = {}
checktipos = db.execute("select id_tipo,nombretipo from tipos")
resultipos = checktipos.fetchall()
for i in resultipos:
    tipos[i[0]] = i[1]


@app.route("/")
def index():
    if not session.get('logged_in'):
        return render_template("login.html")
    else:
        return render_template("main.html")


@app.route("/login", methods=["POST", "GET"])
def loginuser():
    if request.method == "POST":
        userid = request.form.get("userid")
        pssw = request.form.get("userpssw")
        if not pssw:
            checkuser = db.execute(
                "SELECT userpssw, username FROM clients WHERE usernumber like :user or usermail like :user", {'user': userid})
            result = checkuser.fetchone()
            if not result:
                return render_template("/login.html", error=1)
            else:
                session['userid'] = result[1]
                return render_template("/login.html", existid=1, username=result[1])
        else:
            checkpssw = db.execute(
                "SELECT userpssw, nombre, apellido, username, id_client FROM clients WHERE userpssw = :pssw and username=:username", {'pssw': pssw, 'username': session['userid']})
            result = checkpssw.fetchone()
            if not result:
                return render_template("/login.html", error=1, existid=1)
            if result[0] == pssw:
                session.clear()
                session["logged_in"] = True
                session["nombre"] = result[1]
                session["apellido"] = result[2]
                session["username"] = result[3]
                session["idclient"] = result[4]
                return redirect(url_for('home'))
            else:
                return render_template("/login.html", error=1, existid=1)


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        relacion = request.form.get("relacion")
        numero = request.form.get("numero")
        email = request.form.get("email")
        contraseña = request.form.get("pssw")
        db.execute("insert into clients values (default,:username,:nombre,:apellido,:relacion,:usernumber,:usermail,:userpssw)", {
                   'username': username, 'nombre': nombre, 'apellido': apellido, 'relacion': relacion, 'usernumber': numero, 'usermail': email, 'userpssw': contraseña})
        db.commit()
        return redirect(url_for('index'))
    else:
        return render_template("/register.html")


@app.route("/home", methods=["POST", "GET"])
def home():
    if not session.get('logged_in'):
        print("yes")
        return redirect(url_for('index'))
    else:
        checkproductos = db.execute(
            "select nombre, apellido,nombreprod, nombretipo, cantidad, idprod from (clients join (tipos join productos on id_tipo=idtipo) on id_client=idcliente)")
        productos = checkproductos.fetchall()
        return render_template('main.html', productos=productos, tipos=tipos)


@app.route("/publicar", methods=["POST", "GET"])
def publicar():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    else:
        return render_template("publicar.html", tipos=tipos)
    prodname = request.form.get("prodname")
    tipo = request.form.get("tipo")
    cantidad = request.form.get("cantidad")
    db.execute("insert into productos values(default,:prodname,:tipo,:idclient,:cantidad)", {
               'prodname': prodname, 'tipo': tipo, 'idclient': session['idclient'], 'cantidad':cantidad})
    db.commit()
    checkproductos = db.execute(
        "select nombre, apellido,nombreprod, nombretipo, cantidad, idprod from (clients join (tipos join productos on id_tipo=idtipo) on id_client=idcliente)")
    productos = checkproductos.fetchall()
    return render_template('main.html', productos=productos, tipos=tipos)

@app.route("/buscar", methods=["POST"])
def buscar():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    busqueda=request.form.get("buscar")
    query="select nombre, apellido,nombreprod, nombretipo, cantidad, idprod from (clients join (tipos join productos on id_tipo=idtipo and nombreprod like '%"+busqueda+"%') on id_client=idcliente)"
    checkselc=db.execute(query)
    productos=checkselc.fetchall()
    return render_template('main.html', productos=productos, tipos=tipos)

@app.route("/buscarpref", methods=["POST", "GET"])
def buscarpref():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    selected = request.form.get("option")
    checkselec = db.execute("select nombre, apellido,nombreprod, nombretipo, cantidad, idprod from (clients join (tipos join productos on id_tipo=idtipo and id_tipo=:tipo) on id_client=idcliente)",{'tipo':selected})
    productos=checkselec.fetchall()
    return render_template('main.html', productos=productos, tipos=tipos)


@app.route("/gotoproduct/<string:idprod>", methods=["POST", "GET"])
def gotoproduct(idprod):
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    checkinfo = db.execute(
        "select nombre,apellido,nombreprod, nombretipo, cantidad,idprod, id_client, username,relacion, usernumber,usermail  from (clients join (tipos join productos on id_tipo=idtipo and idprod=:idprod) on id_client=idcliente)", {'idprod': idprod})
    product = checkinfo.fetchone()
    if product[6] == session['idclient']:
        checkaccepted = db.execute("select idaccepted,username,nombre,apellido,relacion,usernumber,usermail,nombreprod,nombretipo,cantidad,comentario,oferta from clients join (intereses join (tipos join productos on idtipo=id_tipo) on idprodu=idprod and idprodu=:idprod) on idinteresado=id_client and id_client!=:idclient", {
                                   'idclient': session['idclient'], 'idprod': idprod})
        result = checkaccepted.fetchall()
        if result:
            for i in result:
                if i[0] != None:
                    return render_template('seeproduct.html', product=product, interes=i, used='3', tipos=tipos)
        checkinteres = db.execute(
            "select idinteresado, oferta,comentario,username ,nombre, apellido, idinteres from intereses join clients on idprodu=:idprod and idinteresado=id_client", {'idprod': idprod})
        intereses = checkinteres.fetchall()
        return render_template('seeproduct.html', product=product, interes=intereses, used='2', propio=len(intereses), tipos=tipos)

    checkinteres = db.execute(
        "select idinteresado, idaccepted from intereses where idprodu=:idprod", {'idprod': idprod})
    intereses = checkinteres.fetchall()
    if not intereses:
        return render_template('seeproduct.html', product=product, interes=0, used='0', tipos=tipos)
    for i in intereses:
        if i[0] == session['idclient']:
            if i[1] == None:
                return render_template('seeproduct.html', product=product, interes=len(intereses), used='1', tipos=tipos)
            else:
                return render_template('seeproduct.html', product=product, interes=len(intereses), used='1', accepted=1, tipos=tipos)
        if i[1] != None:
            return render_template('seeproduct.html', product=product, interes=len(intereses), used='1', accepted=1, fan=1, tipos=tipos)
    return render_template('seeproduct.html', product=product, interes=len(intereses), used='0', tipos=tipos)

@app.route("/getproduct/<string:idprod>", methods=["POST","GET"])
def getproduct(idprod):
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    comentario = request.form.get("comment2")
    oferta=request.form.get("oferta")
    oferta+='$'
    db.execute("insert into intereses values(default, :idprod, :comment, :idinter, :oferta, NULL)", {
               'idprod': idprod, 'comment': comentario, 'idinter': session["idclient"], 'oferta':oferta})
    db.commit()
    checkinfo = db.execute(
        "select nombre,apellido,nombreprod, nombretipo, cantidad,idprod from (clients join (tipos join productos on id_tipo=idtipo and idprod=:idprod) on id_client=idcliente)", {'idprod': idprod})
    product = checkinfo.fetchone()
    checkinteres = db.execute(
        "select idinteresado from intereses where idprodu=:idprod", {'idprod': idprod})
    intereses = checkinteres.fetchall()
    for i in intereses:
        if i[0] == session['idclient']:
            return render_template('seeproduct.html', product=product, interes=len(intereses), used='1', tipos=tipos)
    return render_template('seeproduct.html', product=product, interes=len(intereses), used='0', tipos=tipos)

@app.route("/getproductfree/<string:idprod>", methods=["POST", "GET"])
def getfree(idprod):
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    comentario = request.form.get("comment1")
    db.execute("insert into intereses values(default, :idprod, :comment, :idinter, 'Gratis',NULL)", {
               'idprod': idprod, 'comment': comentario, 'idinter': session["idclient"]})
    db.commit()
    checkinfo = db.execute(
        "select nombre,apellido,nombreprod, nombretipo, cantidad,idprod from (clients join (tipos join productos on id_tipo=idtipo and idprod=:idprod) on id_client=idcliente)", {'idprod': idprod})
    product = checkinfo.fetchone()
    checkinteres = db.execute(
        "select idinteresado from intereses where idprodu=:idprod", {'idprod': idprod})
    intereses = checkinteres.fetchall()
    for i in intereses:
        if i[0] == session['idclient']:
            return render_template('seeproduct.html', product=product, interes=len(intereses), used='1', tipos=tipos)
    return render_template('seeproduct.html', product=product, interes=len(intereses), used='0', tipos=tipos)


@app.route("/acceptproduct/<string:idinteres>", methods=["POST", "GET"])
def acceptprod(idinteres):
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    checkinteres = db.execute(
        "select idinteresado from intereses where idinteres=:idinteres ", {'idinteres': idinteres})
    result = checkinteres.fetchone()
    db.execute("insert into aceptados values(default, :idclient, :idinteresado, :idinteres)", {
               'idclient': session['idclient'], 'idinteresado': result[0], 'idinteres': idinteres})
    db.commit()
    checksend = db.execute("select idaceptado from aceptados where idproveedor=:idclient and idreceptor=:idint and idinteres=:idinteres", {
                           'idclient': session['idclient'], 'idint': result[0], 'idinteres': idinteres})
    inputs = checksend.fetchone()
    db.execute("update intereses set idaccepted=:idaccep where idinteres=:idint", {
               'idaccep': inputs[0], 'idint': idinteres})
    db.commit()
    return redirect(url_for('index'))


@app.route("/logout", methods=["GET"])
def logout():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    session["logged_in"] = False
    session.clear()
    return redirect(url_for('index'))
