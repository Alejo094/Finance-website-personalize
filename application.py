import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, lookup, usd


# Algunas de estas funciones fueron brindades por el curso para ayudar en su dificultad como las excepciones y las de seguridad de clave entre otras



# Configurar aplicacion
app = Flask(__name__)

# Asegurar que las interfaces son auto cargados brindadas por el curso
app.config["TEMPLATES_AUTO_RELOAD"] = True


#Esto tambien fue ayudado por google y la universidad
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


app.jinja_env.filters["usd"] = usd


app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configura base de datos
db = SQL("sqlite:///finance.db")


## El codigo realizado en la funcion login que se presenta a continuacion fue modificado por mi en algunas partes para mejorar su interaccion con el usuario


@app.route("/login", methods=["GET", "POST"])
def login():


    # Olvidar el usuario
    session.clear()


    if request.method == "POST":


        if not request.form.get("username"):

            flash("Por favor inserte su usuario!")
            return render_template("login.html")

        elif not request.form.get("password"):

            flash("Por favor inserte su contraseña")
            return render_template("login.html")


        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))


        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")) :

            flash("Contraseña o/y usuario incorrectos")
            return render_template("login.html")


        # Recuerda que usuario inicio sesion
        session["user_id"] = rows[0]["id"]


        return redirect("/")


    else:
        return render_template("login.html")



@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


### Hasta esta linea el codigo fue brindado por el curso para ayudar en la dificultad del problema

## A partir de aca todas las funciones, logica y demas codigos fueron completamente realizados por mi 100%

@app.route("/")
@login_required
def index():

    val = [['Agosto',5,2021], ['Agosto',6,2021], ['Agosto',7,2021]]

    users_cash_track_table = db.execute("SELECT symbol, name, SUM(shares) as totalShares,price,SUM(total) as totalbought FROM users_cash_track WHERE id=:id GROUP BY symbol HAVING totalShares >0",id=session["user_id"] )

    cash_left = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])

    stock_boug = db.execute("SELECT stock_boug FROM final_tracker WHERE id=:id",id=session["user_id"])

    money_accout= db.execute("SELECT money_accout FROM final_tracker WHERE id=:id",id=session["user_id"])

    return render_template("index.html",users_cash_track_table=users_cash_track_table, cash_left = cash_left, stock_boug=stock_boug, money_accout=money_accout,val=val)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():


    symbol= request.form.get("symbol")

    shares=request.form.get("shares")

    total_stock_boug = 0

    val = [['Agosto',5,2021], ['Agosto',6,2021], ['Agosto',7,2021]]


    if request.method =="POST":

        stock_info=lookup(symbol)

        if not symbol:

            flash("Por favor ingrese el simbolo de la accion que desea compra","error")

            return render_template("buy.html", val=val)

        if not shares:

            flash("Por favor ingrese el numero de acciones que desea comprar","error")

            return render_template("buy.html", val=val)

        else:

            try:
                num_shares= int(request.form.get("shares"))

            except ValueError:

                flash("Por favor ingrese el numero de acciones que desea comprar","error")

                return render_template("buy.html", val=val)

        if stock_info == None:

            flash("La accion que esta tratando de comprar no existe con ese simbolo","error")

            return render_template("buy.html", val=val)

        if num_shares <= 0:

            flash("Recuerde que la compra de acciones es con numeros positivos mayores a cero","error")

            return render_template("buy.html", val=val)


        cash_left= db.execute("SELECT cash FROM users WHERE id=:id",id=session["user_id"])

        x = db.execute("SELECT stock_boug FROM final_tracker WHERE id=:id",id=session["user_id"])

        name_stock= stock_info["name"]

        price_stock =stock_info["price"]

        stock_bought = num_shares * price_stock

        total_after_purchase =  cash_left[0]["cash"] - stock_bought


        if total_after_purchase < 0:

            flash("No tiene suficiente dinero en su cuenta para comprar estas acciones por favor revise su saldo y el valor total de la compra!","error")

            return render_template("buy.html", val=val)


        total_stock_boug =  x[0]["stock_boug"] + stock_bought

        total_money_account =   total_stock_boug + total_after_purchase

        id=session["user_id"]



        db.execute("UPDATE users SET cash=:total_after_purchase WHERE id=:id",total_after_purchase=total_after_purchase,id=session["user_id"])

        db.execute("INSERT INTO users_cash_track (id,symbol,name,shares,price,total,total_stock_boug,total_after_purchase) VALUES (?,?,?,?,?,?,?,?)",id,symbol,name_stock,num_shares,price_stock,stock_bought,total_stock_boug,total_after_purchase)

        db.execute("UPDATE final_tracker SET stock_boug=:total_stock_boug WHERE id=:id",total_stock_boug=total_stock_boug, id=session["user_id"])

        db.execute("UPDATE final_tracker SET money_accout=:total_money_account WHERE id=:id",total_money_account=total_money_account,id=session["user_id"])


        flash("ACCION/ES COMPRADAS!","error")

        return redirect("/")


    return render_template("buy.html",  val=val)


@app.route("/history")
@login_required
def history():


    val = [['Agosto',5,2021], ['Agosto',6,2021], ['Agosto',7,2021]]

    transactions = db.execute("SELECT symbol, name,shares,price,transac_d FROM users_cash_track WHERE id=:id",id=session["user_id"] )

    for i in range(len(transactions)):
        transactions[i]["price"] = transactions[i]["price"]

        return render_template("history.html",transactions=transactions,val=val)

    return render_template("history.html",transactions=transactions,val=val)


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():

    val = [['Agosto',5,2021], ['Agosto',6,2021], ['Agosto',7,2021]]

    symbol= request.form.get("symbol")

    if request.method =="POST":

        stock_info=lookup(symbol)

        if stock_info!= None:

            return render_template("quoted.html",stock_info = stock_info,val=val)

        else:

            flash("La accion que esta tratando de cotizar no existe con este simbolo por favor revise","error")

            return render_template("quote.html",val=val)


    return render_template("quote.html", val=val)


@app.route("/register", methods=["GET", "POST"])
def register():


    def username_length(username):

        if username == '':

            return 0

        else:

            return 1 + username_length(username[1:])


    def password_length(password):

        if password == '':

            return 0

        else:

            return 1 +password_length(password[1:])



    if request.method == "POST":

        username = request.form.get("username")

        user_exist= db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if not username:

            flash("Por favor cree un usuario para su cuenta")

            return render_template("register.html")



        elif len(user_exist) != 0:

            flash("Este usuario ya existe en nuestras bases de datos por favor intente con otro")

            return render_template("register.html")



        password = request.form.get("password")

        if not password:

            flash("Por favor cree una clave para su cuenta")

            return render_template("register.html")


        confirmation = request.form.get("confirmation")

        if not confirmation:

            flash("Por favor confirme su contraseña")

            return render_template("register.html")


        if password != confirmation:

            flash("La contraseña y la confirmacion no coinciden por favor revise")

            return render_template("register.html")


        if password_length(password)>=20:

            flash("Por favor cree una clave menor a 20 caracteres")

            return render_template("register.html")


        if username_length(username)>=20:

            flash("Por favor cree un usuario con menos caracteres es muy largo el que quiere crear")

            return render_template("register.html")


        hash_passw = generate_password_hash(password)

        db.execute("INSERT INTO users (username,hash) VALUES (?,?) ",username,hash_passw)

        stock_boug=0
        money_accout=10000

        db.execute("INSERT INTO final_tracker (stock_boug,money_accout) VALUES (?,?)",stock_boug,money_accout )

        flash("Usuario Creado! Inicie sesion para ver todos los beneficios que trae esta comunidad!","error")

    return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():

    val = [['Agosto',5,2021], ['Agosto',6,2021], ['Agosto',7,2021]]


    stocks_own = db.execute("SELECT symbol FROM users_cash_track WHERE id=:id GROUP BY symbol HAVING SUM(shares) >0",id=session["user_id"])

    if request.method == "POST":

        symbol=request.form.get("symbol")

        if not symbol:

            flash("Por favor revise que el simbolo insertado este correctamente elegido ")

            return render_template("sell.html", stocks_own= stocks_own,val=val)


        num_shares= request.form.get("shares")

        try:
            num_shares= int(request.form.get("shares")) *(-1)

        except ValueError:

            flash("Por favor ingrese un valor que no sea decimal y sea un numero entero")

            return render_template("sell.html", stocks_own= stocks_own,val =val)


        if num_shares >=0:

            flash("Por favor ingrese un valor de un numero positivo")

            return render_template("sell.html", stocks_own= stocks_own,val =val)



        stock_info=lookup(symbol)

        total_sell = num_shares * stock_info["price"]

        id=session["user_id"]

        name_stock= stock_info["name"]

        price_stock =stock_info["price"]

        stock_bought = num_shares * price_stock



        stock_boug = db.execute("SELECT stock_boug FROM final_tracker WHERE id=:id",id=session["user_id"])

        money_accout= db.execute("SELECT money_accout FROM final_tracker WHERE id=:id",id=session["user_id"])

        cash_left = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])

        total_stock_boug =  stock_boug[0]["stock_boug"] + stock_bought

        total_after_purchase =  cash_left[0]["cash"] - stock_bought

        stocks_ownN = db.execute("SELECT symbol, SUM(shares) as total1 FROM users_cash_track WHERE id=:id GROUP BY symbol HAVING symbol=:symbol",id=session["user_id"],symbol=request.form.get("symbol"))

        final=stocks_ownN[0]["total1"] + num_shares

        total_money_account = total_stock_boug + total_after_purchase

        if final >= 0:

            db.execute("UPDATE users SET cash=:total_after_purchase WHERE id=:id",total_after_purchase=total_after_purchase,id=session["user_id"])

            db.execute("INSERT INTO users_cash_track (id,symbol,name,shares,price,total, total_stock_boug,total_after_purchase) VALUES (?,?,?,?,?,?,?,?)",id,symbol,name_stock,num_shares,price_stock,stock_bought,total_stock_boug,total_after_purchase)

            db.execute("UPDATE final_tracker SET stock_boug=:total_stock_boug WHERE id=:id",total_stock_boug=total_stock_boug, id=session["user_id"])

            db.execute("UPDATE final_tracker SET money_accout=:total_money_account WHERE id=:id",total_money_account=total_money_account,id=session["user_id"])

            cash_left = db.execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])

            stock_boug = db.execute("SELECT stock_boug FROM final_tracker WHERE id=:id",id=session["user_id"])

            money_accout = db.execute("SELECT money_accout FROM final_tracker WHERE id=:id",id=session["user_id"])

            users_cash_track_table = db.execute("SELECT symbol, name, SUM(shares) as totalShares,price,SUM(total) as totalbought FROM users_cash_track WHERE id=:id GROUP BY symbol HAVING SUM(shares) >0",id=session["user_id"] )

            flash("Acciones Vendidas!")

            return render_template("index.html",users_cash_track_table=users_cash_track_table, cash_left = cash_left, stock_boug =stock_boug , money_accout=money_accout,val =val)

        else:

            flash("Usted no posee esa cantidad total de acciones por favor revise su portafolio y intente de nuevo")

            return render_template("sell.html", stocks_own= stocks_own,val=val)


    return render_template("sell.html", stocks_own= stocks_own, val=val)




