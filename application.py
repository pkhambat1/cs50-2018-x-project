# A simple TODO app that lets you add TODO items and check them off, hopefully helping your productivity
# This project helped me learn a lot about JQuery, Ajax and Flask
# Updated to include a "Goals" tab which I had wanted from the start

import os

from cs50 import SQL
import datetime
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
import re
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///doneanddone.db")

# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (insted of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
@login_required
def index():
    """Show reminders"""

    reminders = db.execute("SELECT * FROM reminders WHERE user_id = :user_id",
                           user_id=session["user_id"])

    users = db.execute("SELECT * FROM users WHERE id = :user_id",
                       user_id=session["user_id"])

    firstname = users[0]["firstname"]

    return render_template("index.html", reminders=reminders, name=firstname)


@app.route("/goals")
@login_required
def goals():
    """Show goals"""

    goals = db.execute("SELECT * FROM goals WHERE user_id = :user_id",
                       user_id=session["user_id"])

    return render_template("goals.html", goals=goals)


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

        # User reached route via POST (as by submitting a form via POST)
        users = db.execute("SELECT * FROM users WHERE username = :username",
                           username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(users) != 1 or not check_password_hash(users[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = users[0]["id"]

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


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Forget any user_id
        session.clear()

        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure all fields are filled
        if not firstname:
            return apology("Missing first name!")
        elif not username:
            return apology("Missing username!")
        elif not password:
            return apology("Missing password!")
        elif not confirmation:
            return apology("Missing password confirmation!")

        # Ensure password matches confirmation
        elif password != confirmation:
            return apology("Password and confirmation do not match!")

        # Hash password
        hashed_password = generate_password_hash(password)

        # Ensure username is unique
        username_check = db.execute("SELECT * FROM users WHERE username = :username",
                                    username=username)
        if username_check:
            return apology("Username taken, please select different username")

        # Add user to database

        db.execute("INSERT INTO users (firstname, lastname, username, hash) VALUES (:firstname, :lastname, :username, :hashed_password)",
                   firstname=firstname, lastname=lastname, username=username, hashed_password=hashed_password)

        # Automatically login user
        # Query database for username
        users = db.execute("SELECT * FROM users WHERE username = :username",
                           username=username)

        # Remember which user has logged in
        session["user_id"] = users[0]["id"]

        # Alert
        flash("Welcome to Done&Done!")
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    """Change password"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        new_confirmation = request.form.get("new_confirmation")

        # Ensure all fields are filled
        if not old_password:
            return apology("Missing old password!")

        # Hash old password
        hashed_old_password = generate_password_hash(old_password)
        print(hashed_old_password)

        # Query database for users
        users = db.execute("SELECT * FROM users WHERE id = :user_id",
                           user_id=session["user_id"])

        print(users[0]["hash"])

        # Ensure old password is correct
        if not check_password_hash(users[0]["hash"], old_password):
            return apology("Incorrect password!")

        # Ensure other fields are filled
        elif not new_password:
            return apology("Missing new password!")
        elif not new_confirmation:
            return apology("Missing new password confirmation!")

        # Ensure password matches confirmation
        elif new_password != new_confirmation:
            return apology("Password and confirmation do not match!")

        # Hash new password
        hashed_new_password = generate_password_hash(new_password)
        print(hashed_new_password)

        # Ensure new password is not same as old password
        if check_password_hash(users[0]["hash"], new_password):
            return apology("New password matches current password, please enter different password!")

        # Change password
        db.execute("UPDATE users set hash = :hashed_new_password WHERE id = :user_id",
                   hashed_new_password=hashed_new_password, user_id=session["user_id"])

        # Flash message
        flash("Password change successful!")
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change.html")


@app.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create New Reminder"""
    if request.method == "POST":

        reminder = request.form.get("reminder")
        details = request.form.get("details")

        if not reminder:
            return apology("Missing Reminder")

        # Insert reminder
        db.execute("INSERT INTO reminders (name, details, user_id) VALUES (:reminder, :details, :user_id)",
                   reminder=reminder, details=details, user_id=session["user_id"])

        return redirect("/")

    else:
        return render_template("new.html")


@app.route("/new_goal", methods=["GET", "POST"])
@login_required
def new_goal():
    """Create New Goal"""
    if request.method == "POST":

        goal = request.form.get("goal")
        details = request.form.get("details")

        if not goal:
            return apology("Missing Goal")

        # Insert reminder
        db.execute("INSERT INTO goals (name, details, user_id) VALUES (:goal, :details, :user_id)",
                   goal=goal, details=details, user_id=session["user_id"])

        return redirect("/goals")

    else:
        return render_template("new_goal.html")


@app.route("/checked", methods=["POST"])
@login_required
def checked():
    """Update reminders & completed tables with checked data
    and return new list of reminders asjson object to ajax"""

    checked_reminders = request.form.getlist("check_reminder")

    for checked_item in checked_reminders:
        print(checked_item, "checked_item")
        checked_reminder = db.execute("SELECT * FROM reminders WHERE id = :checked",
                                      checked=checked_item)
        checked_reminder = checked_reminder[0]

        # Insert into completed
        db.execute("INSERT INTO completed (name, details, user_id) VALUES (:name, :details, :user_id)",
                   name=checked_reminder['name'], details=checked_reminder['details'], user_id=checked_reminder['user_id'])
        # Delete from reminders
        db.execute("DELETE FROM reminders WHERE id = :reminder_id",
                   reminder_id=checked_reminder['id'])

        # Get updated reminders
        reminders = db.execute("SELECT * FROM reminders WHERE user_id = :user_id",
                               user_id=session["user_id"])

    print(checked_reminders, "checked_reminders")

    return (jsonify(reminders))


@app.route("/checked_goal", methods=["POST"])
@login_required
def checked_goal():
    """Update goals & completed tables with checked data
    and return new list of reminders asjson object to ajax"""

    checked_goals = request.form.getlist("check_goal")

    for checked_goal in checked_goals:

        checked_goal = db.execute("SELECT * FROM goals WHERE id = :checked",
                                  checked=checked_goal)
        checked_goal = checked_goal[0]

        # Insert into completed
        db.execute("INSERT INTO completed (name, details, user_id) VALUES (:name, :details, :user_id)",
                   name=checked_goal['name'], details=checked_goal['details'], user_id=checked_goal['user_id'])
        # Delete from reminders
        db.execute("DELETE FROM goals WHERE id = :goal_id",
                   goal_id=checked_goal['id'])

        # Get updated reminders
        goals = db.execute("SELECT * FROM goals WHERE user_id = :user_id",
                           user_id=session["user_id"])

    print(checked_goals, "checked_goals")

    return (jsonify(goals))


@app.route("/completed")
@login_required
def completed():
    """Show completed tasks"""
    completed = db.execute("SELECT * FROM completed WHERE user_id = :user_id",
                           user_id=session["user_id"])

    return render_template("completed.html", completed=completed)


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)