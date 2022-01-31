from asyncio import SendfileNotAvailableError
from crypt import methods
import os
import email
from turtle import title

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for
from itsdangerous import URLSafeTimedSerializer 
from flask_mail import Mail, Message
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
from mail import confirmmail, confirm_email

# Configure application
app = Flask(__name__)

app.config['DEBUG'] = True
app.config['TESTING'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
# app.config['MAIL_DEBUG'] = True
app.config['MAIL_USERNAME'] = 'Seenit302@gmail.com'
app.config['MAIL_PASSWORD'] = 'Purabiart@302'
app.config['MAIL_DEFAULT_SENDER'] = ('SeenIt.com', 'Seenit302@gmail.com')
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
            db.execute("CREATE TABLE ?(id INTEGER NOT NULL , name TEXT, seen INTEGER, total INTEGER, type TEXT NOT NULL, source TEXT, time DATETIME, times INTEGER, PRIMARY KEY(id))",name)
            
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
def addupdate():
    name = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']
    if request.method == 'GET': 
        return render_template("addupdate.html", table=db.execute("SELECT * FROM ?", name))
    if request.method == 'POST':
        title = request.form.get("name")
        seen = request.form.get("seen")
        total = request.form.get("total")
        type = request.form.get("type")
        time = datetime.now()
        source = request.form.get("source")
        times = request.form.get("times")
        db.execute("INSERT INTO ?(name, seen, total, type, source, time, times) VALUES(?, ?, ?, ?, ?, ?, ?)", name, title, seen, total, type, source, time, times)
        return render_template("addupdate.html", table=db.execute("SELECT * FROM ?", name))

@app.route('/seenupdate')
def seenupdate():
    return render_template("addupdate.html", table=db.execute("SELECT * FROM ?", name))

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == 'GET':
        return render_template("search.html")
    if request.method == 'POST':
        name = request.form.get("name")
        return render_template("results.html", results=lookup(name)) 
