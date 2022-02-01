from asyncio import SendfileNotAvailableError
from crypt import methods
import os
import email
# from turtle import title
from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for

# Configure application
app = Flask(__name__)

from itsdangerous import URLSafeTimedSerializer 
from flask_mail import Mail, Message
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, lookupanime, usd
from mail import confirmmail, confirm_email


app.config['DEBUG'] = True
app.config['TESTING'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
# app.config['MAIL_DEBUG'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = ('SeenIt.com', os.getenv("MAIL_USERNAME"))
app.config['MAIL_MAX_EMAILS'] = None
# app.config['MAIL_SUPRESS_SEND'] = False
app.config['MAIL_ASCII_ATTACHMENTS'] = False

mail = Mail(app)
s = URLSafeTimedSerializer('SECRET_KEY')


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///SeenIt.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session['user_name'] = rows[0]["username"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/")
@login_required
def index():
    # return render_template("index.html", table=db.execute("SELECT * FROM ?", session['user_id']))
    name = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
    return render_template("index.html", table=db.execute("SELECT * FROM ?", name))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("username")
        password = request.form.get("password")
        # Checking password and confirmation
        confirmation = request.form.get("confirmation")
        if not name:
            return apology("Must Provide Username")
        user = []
        # Checking if the username already exists
        lis = db.execute("SELECT username FROM users")
        for row in lis:
            user.append(row["username"])
        if name in user:
            return apology("USERNAME already exists")
        if not password or not confirmation or password != confirmation:
            return apology("Must Provide Correct Password And Confirmation")
        else:

            # adding the new user to users table
            token = s.dumps(name, salt='email-confirm')
            msg = Message('Confirm_Email', recipients=[name])
            link = url_for('confirm_email', token=token, external=True)
            msg.body = 'Your link is {}'.format(link)
            mail.send(msg)
            db.execute("INSERT INTO users(username, hash, tablename, confirmation) VALUES(?, ?, ?, 0);", name, generate_password_hash(password), name)
            db.execute("INSERT INTO personalinfo(id, profilepic) VALUES(?, 0);", db.execute("SELECT id FROM users WHERE username = ?", name)[0]['id'])
            db.execute("CREATE TABLE ?(id INTEGER NOT NULL , name TEXT, seen INTEGER, total INTEGER, type TEXT NOT NULL, time DATETIME, time_per_episode FLOAT, times INTEGER, PRIMARY KEY(id))",name)
            db.execute("INSERT INTO ?(name, type,seen, total, time_per_episode, times) VALUES('sample', 'manga', 0, 0, 0, 0);", name)
            #hello = confirmmail(name)
            #return hello

            return redirect("/")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route('/confirm_email/<token>')
def confirm_email(token):
    email = s.loads(token, salt = 'email-confirm', max_age = 3600)
    db.execute("UPDATE users SET confirmation = 1 WHERE username =?", email)
    return 'Your Email Has been confirmed'

@app.route('/addupdate', methods = ['GET', 'POST'])
@login_required
def addupdate():
    name = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
    if request.method == 'GET': 
        return render_template("addupdate.html", table=db.execute("SELECT * FROM ?", name))
    if request.method == 'POST':
        title = request.form.get("name")
        if not title:
            return apology("Must Provide Title")
        seen = request.form.get("seen")
        if not seen:
            seen = 0
        total = request.form.get("total")
        if not total:
            total = 0
        type = request.form.get("type")
        if type == 'Choose...':
            return apology("Must Provide Type")
        tpe = request.form.get("tpe")
        time = datetime.now()
        times = request.form.get("times")
        if not times:
            times = 0
        if not tpe:
            if type == "manga":
                tpe = 3
            elif type == "anime":
                tpe = 24
            elif type == "television":
                tpe = 60
            elif type == "asiandrama":
                tpe = 60
            else:
                tpe = 60
        db.execute("INSERT INTO ?(name, seen, total, type, time, time_per_episode, times) VALUES(?, ?, ?, ?, ?, ?, ?)", name, title, seen, total, type, time, float(tpe), times)
        return render_template("addupdate.html", table=db.execute("SELECT * FROM ?", name))

@app.route('/seenupdate')
def seenupdate():
    return render_template("addupdate.html", table=db.execute("SELECT * FROM ?", name))

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == 'GET':
        return render_template("search.html")
    if request.method == 'POST':
        name = request.form.get("name")
        return render_template("results.html", results=lookup(name)) 

@app.route("/searchanime", methods=["GET", "POST"])
@login_required
def searchanime():
    if request.method == 'GET':
        return render_template("search.html")
    if request.method == 'POST':
        name = request.form.get("name")
        return render_template("resultsanime.html", results=lookupanime(name))

@app.route("/changepass", methods=["GET", "POST"])
@login_required
def changepass():
    if request.method == "GET":
        return render_template("change.html")
    # When the user entered information
    if request.method == "POST":
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        # checking if confirmation is correct or null op password is null
        if not password or not confirmation or password != confirmation:
            return apology("Must Provide Password And Correct Confirmation")
        db.execute("UPDATE users SET hash = ?", generate_password_hash(password))
    return redirect("/")

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    if request.method == "GET":
        return render_template("change.html", personalinfo=db.execute("SELECT * FROM personalinfo WHERE id = ?", session['user_id'])[0])
    if request.method == "POST":
        column = request.form.get("column")
        data = request.form.get("data")
        db.execute("UPDATE personalinfo SET ? = ? WHERE id = ?", column, data, session['user_id'])
        return render_template("change.html", personalinfo=db.execute("SELECT * FROM personalinfo WHERE id = ?", session['user_id'])[0])

@app.route("/myself")
@login_required
def myself():
    name = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
    timee=db.execute("SELECT sum((time_per_episode * seen)) AS typesum from ? group by type ORDER BY typesum DESC LIMIT 1;", name)[0]['typesum']
    length = float(2.5 ** (len(str(timee)) - 2))
    if length == 0:
        length = 1
    return render_template("myself.html", personalinfo=db.execute("SELECT * FROM personalinfo WHERE id = ?", session['user_id'])[0], time_type=db.execute("SELECT sum((time_per_episode * seen)*times) / ? AS typesum, sum((time_per_episode * seen)*times)/60.0 as types, type, type from ? group by type;", length, name), total_time=db.execute("SELECT sum((time_per_episode * seen * times)/60) AS TOTALSUM from ?;", name)[0])

@app.route('/update', methods = ["POST"])
@login_required
def update():
    id = request.form.get('id')
    seen = request.form.get('seen')
    type = request.form.get('type')
    name = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
    db.execute("UPDATE ? SET ? = ? WHERE id = ?", name, type, seen, id)
    return render_template("addupdate.html", table=db.execute("SELECT * FROM ?", name))

@app.route('/delete', methods = ["POST"])
@login_required
def delete():
    id = request.form.get('id')
    name = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
    db.execute("DELETE FROM ? WHERE id = ?", name, id)
    return render_template("addupdate.html", table=db.execute("SELECT * FROM ?", name))

@app.route('/localsearch', methods = ["POST"])
def localsearch():
    q = request.form.get('query')
    search = f"%{q}%"
    name = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
    table = db.execute("SELECT * FROM ? WHERE name LIKE ?", name, search)
    return render_template("index.html", table=table)

@app.route('/usersearch', methods=["GET", "POST"])
def usersearch():
    if request.method == "GET":
        return render_template("usrsrch.html")
    if request.method == "POST":
        name = request.form.get("username")
        timee=db.execute("SELECT sum((time_per_episode * seen)) AS typesum from ? group by type ORDER BY typesum DESC LIMIT 1;", name)[0]['typesum']
        length = float(2.5 ** (len(str(timee)) - 2))
        id = db.execute("SELECT id FROM users WHERE username = ?", name)[0]['id']
        return render_template("userresult.html", table=db.execute("SELECT * FROM ?", name), personalinfo=db.execute("SELECT * FROM personalinfo WHERE id = ?", id)[0], time_type=db.execute("SELECT sum((time_per_episode * seen)*times) / ? AS typesum, sum((time_per_episode * seen)*times)/60.0 as types, type, type from ? group by type;", length, name), total_time=db.execute("SELECT sum((time_per_episode * seen * times)/60) AS TOTALSUM from ?;", name)[0])
