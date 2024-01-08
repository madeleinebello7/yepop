import os

from cs50 import SQL
from datetime import date
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///yepop.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Homepage
@app.route("/")
@login_required
def index():
    """Show items up for sale"""
    items = db.execute("SELECT * FROM items")
    number_items = len(items)
    items_divided = [items[x:x+3] for x in range(0, number_items, 3)]

    return render_template("index.html", number_items=number_items, items=items_divided)


# Sell an item
@app.route("/sell", methods=["GET", "POST"])
def sell():
    if request.method == "GET":
        return render_template("sell.html")

    else:
        # Retrieve the inputted data
        name = request.form.get("name")
        photo = request.form.get("image")
        category = request.form["category"]
        condition = request.form["condition"]
        size = request.form["size"]
        color = request.form["color"]

        # Add item to db
        db.execute("INSERT INTO items (seller_id, name, photo, category, condition, size, color) VALUES (?,?,?,?,?,?,?)",
                   session["user_id"], name, photo, category, condition, size, color)

        # Information for template
        message = "Congratulations, you just uploaded"
        link = "sell"
        button = "Upload more"

        return render_template("success.html", name=name, photo=photo, message=message, link=link, button=button)

# Search an item
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return render_template("search.html")
    else:
        # Retrieve the inputted data
        category = request.form["category"]
        condition = request.form["condition"]
        size = request.form["size"]
        color = request.form["color"]

        # Query through database
        items = db.execute(
            "SELECT item_id, name, photo FROM items WHERE category=? and condition=? and size=? and color=?", category, condition, size, color)
        print(items)
        for item in items:
            item["item_id"] = str(item["item_id"])
        number_items = len(items)
        items_divided = [items[x:x+3] for x in range(0, len(items), 3)]

        return render_template("searched.html", items=items_divided, number_items=number_items)


# Load messages
@app.route("/messages")
def messages():
    # Query database for messages received
    messages = db.execute(
        "SELECT content, sender FROM messages WHERE receiver=? ORDER BY message_id DESC", session["user_id"])

    # Finds username of sender
    for message in messages:
        print("Message: ", message)
        sender = db.execute(
            "SELECT username FROM users WHERE id=?", message["sender"])
        sender = sender[0]["username"]
        message["sender_username"] = sender
    number_messages = len(messages)

    return render_template("messages.html", messages=messages, number_messages=number_messages)

# Login


@app.route("/login", methods=["GET", "POST"])
def login():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Searches db for username and ensures password is correct
        rows = db.execute("SELECT * FROM users WHERE username =?",
                          request.form.get("username"))
        if len(rows) != 1:
            return render_template("login.html", username_error="This username does not exist")
        elif not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", password_error="Password is incorrect")

        # Remember logged in user
        session["user_id"] = rows[0]["id"]

        return redirect("/")

    # User reached page by GET
    else:
        return render_template("login.html")

# Register user


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    else:
        # Retrieve data from form
        username = request.form.get("username")
        username_query = db.execute(
            "SELECT * FROM users WHERE username=?", username)
        password = request.form.get("password")
        password_confirmation = request.form.get("password_confirmation")
        email = request.form.get("email")
        phone = request.form.get("phone")

        # Check that inputted data is correct
        if len(username_query) > 0:
            error = "'" + username + "' is already taken. Try another username"
            return render_template("register.html", username_error=error)
        elif password != password_confirmation:
            return render_template("register.html", password_error="Password and password confirmation must match")

        # Insert user into database
        hashed_password = generate_password_hash(password)
        db.execute("INSERT INTO users (username, email, phone, hash) VALUES (?,?,?,?)",
                   username, email, phone, hashed_password)

        # Remember user
        username_query = db.execute(
            "SELECT * FROM users WHERE username=?", username)
        session["user_id"] = username_query[0]["id"]

        return redirect("/")

# Claim an item
@app.route("/claim", methods=["POST"])
def claim():
    if request.method == "POST":
        item_id = int(request.form.get("item"))
        name = request.form.get("name")

        # Get item image
        photo = db.execute("SELECT photo FROM items WHERE item_id=?", item_id)
        photo = photo[0]["photo"]

        # Get seller id
        seller_id = db.execute(
            "SELECT seller_id FROM items WHERE item_id=?", item_id)
        seller_id = seller_id[0]["seller_id"]
        seller_info = db.execute(
            "SELECT email, phone, username FROM users WHERE id=?", seller_id)

        # Get claimer info
        claimer_info = db.execute(
            "SELECT email, phone, username FROM users WHERE id=?", session["user_id"])

        # Add item to transactions
        today = date.today()
        today = today.strftime("%d/%m/%Y")
        db.execute("INSERT INTO transactions (item_id, seller_id, claimer_id, date, name) VALUES (?,?,?,?,?)",
                   item_id, seller_id, session["user_id"], today, name)
        transaction_id = db.execute(
            "SELECT transaction_id FROM transactions WHERE item_id=?", item_id)
        transaction_id = transaction_id[0]["transaction_id"]

        # Delete item from database
        db.execute("DELETE FROM items WHERE item_id=?", item_id)

        # Send message to claimer
        message_claimer = "Congratulations! You just claimed the object '" + name + \
            "'. Contact the seller to set up a meet-up and claim your item.\nEmail: " + \
            seller_info[0]["email"] + "\nPhone: " + seller_info[0]["phone"] + \
            "\nUsername: " + seller_info[0]["username"]
        db.execute("INSERT INTO messages (sender, receiver, content, transaction_id) VALUES (?,?,?,?)",
                   seller_id, session["user_id"], message_claimer, transaction_id)

        # Send message to seller
        message_seller = "Congratulations! Someone just claimed your object '" + name + \
            "'. Contact the claimer to set up a meet-up to give him your item.\nEmail: " + \
            claimer_info[0]["email"] + "\nPhone: " + claimer_info[0]["phone"] + \
            "\nUsername: " + claimer_info[0]["username"]
        db.execute("INSERT INTO messages (sender, receiver, content, transaction_id) VALUES (?,?,?,?)",
                   session["user_id"], seller_id, message_seller, transaction_id)

        # Information for template
        message = "Congratulations, you just claimed"
        link = "search"
        button = "Search more"

        return render_template("success.html", name=name, message=message, photo=photo, link=link, button=button)

# Log out user
@app.route("/logout")
def logout():

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# Load items uploaded by user
@app.route("/myitems")
def myitems():
    myitems = db.execute(
        "SELECT * FROM items WHERE seller_id=?", session["user_id"])
    number_items = len(myitems)
    items_divided = [myitems[x:x+3] for x in range(0, number_items, 3)]

    return render_template("myitems.html", items=items_divided, number_items=number_items)


# Delete item
@app.route("/delete", methods=['POST'])
def delete():
    item_id = request.form.get("item")
    db.execute("DELETE FROM items WHERE item_id=?", item_id)
    return redirect("/myitems")


# Send a message
@app.route("/message", methods=["POST"])
def message():
    # Retrieves information about sender, receiver, content
    sender_id = session["user_id"]
    username_receiver = request.form.get("username")
    message = request.form.get("message")
    receiver_id = db.execute(
        "SELECT id FROM users WHERE username=?", username_receiver)

    # Checks if receiver exists
    if len(receiver_id) == 0:
        return redirect("/messages")
    receiver_id = receiver_id[0]["id"]

    # Adds message to database
    db.execute(
        "INSERT INTO messages (sender, receiver, content, transaction_id) VALUES (?,?,?,?)", sender_id, receiver_id, message, 0)

    return redirect("/messages")
