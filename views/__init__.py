from . import login
from core import app
from flask import redirect, render_template

@app.route('/')
def ind():
    #return render_template('generic_error_final.html')
    return redirect('/login')

from .login import login, logout, login_required
app.route('/login', methods=["POST", "GET"])(login)
app.route('/logout', methods=["POST", "GET"])(logout)

from .inicio import inicio, votar
app.route('/inicio', methods=["Get"])(inicio)
app.route('/votar', methods=["POST"])(votar)

@app.route('/error')
def errro():
    return render_template("generic_error.html")

@app.errorhandler(Exception)
def handle_exception(e):
    print(e)
    return render_template("generic_error.html")


