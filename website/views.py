from flask import Blueprint,render_template
views=Blueprint('views',__name__)


@views.route('/')
def Base():
  return render_template("home.html")


@views.route('/profile')
def profile():
    user = {
        "name": "Hamza Madi",
        "address": "Physical Address",
        "profession": "Plumber",
        "experience": "Expert"
    }
    return render_template("userProfile.html", user=user)
