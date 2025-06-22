from flask import Blueprint, render_template
from .models import User

views = Blueprint('views', __name__)

@views.route('/')
def Base():
    return render_template("home.html")

@views.route('/profile/<int:user_id>')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template("userProfile.html", user=user)
