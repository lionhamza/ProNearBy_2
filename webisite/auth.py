from flask import Blueprint
auth=Blueprint('auth',__name__)

@auth.route('/login')
def login():
    return "<h1>Login<h1>"

@auth.route('/logout')
def logout():
    return "<h1>Logout<h1>"

@auth.route('/SingUp')
def singUp():
    return "<h1>singUp<h1>"