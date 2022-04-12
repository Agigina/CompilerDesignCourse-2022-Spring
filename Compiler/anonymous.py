from flask import Blueprint, render_template

blue_print = Blueprint('blue_print',__name__)

@blue_print.route('/')
def index():
    return render_template('main.html')
