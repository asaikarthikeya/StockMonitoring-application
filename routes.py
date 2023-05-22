from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    url_for,
    session
)

from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError


from flask_bcrypt import Bcrypt,generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from app import create_app,db,login_manager,bcrypt
from models import User
from forms import login_form,register_form

from flask import Flask, render_template,request
import requests
import matplotlib.pyplot as plt
import io
import base64
from flask_sqlalchemy import SQLAlchemy
from flask import jsonify, request
from models import Watchlist 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)


@app.route('/', methods=['GET', 'POST'])
def index1():    
    return render_template('index.html', title="Home")

@app.route('/submit', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Retrieve the selected symbol from the form data
        symbol = request.form.get('symbol')

        # Make API request to Alpha Vantage
        api_key = 'VMM3EIHNMOHO1F2M'  # Replace with your Alpha Vantage API key
        interval = '60min'  # Replace with the desired interval
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={api_key}'
        response = requests.get(url)

        # Process the API response
        if response.status_code == 200:
            data = response.json()
            # Extract the relevant stock prices from the response
            # Example: closing prices for the last 10 data points
            time_series = data['Time Series (60min)']
            closing_prices = [float(time_series[key]['4. close']) for key in sorted(time_series.keys(), reverse=True)[:10]]

            # Create the plot
            plt.figure(figsize=(8, 6))
            plt.plot(closing_prices)
            plt.xlabel('Time')
            plt.ylabel('Closing Price')
            plt.title('Stock Prices')

            # Convert the plot to an image for embedding in HTML
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()
            plt.close()
            return render_template('index.html', plot_url=plot_url, title="Home", symbol=symbol)
        else:
            return f'Error: {response.status_code}'
    else:
        # Render the initial HTML template without a plot
        return render_template('index.html', title="Home")

@app.before_first_request
def create_tables():
    db.create_all()

# @app.route('/watchlist')
# def watchlist():
#     user_id = current_user.id
#     user = User.query.get(int(user_id))

#     watchlist_count = len(user.watchlists)
#     watchlist_data = []

#     for watchlist in user.watchlists:
#         watchlist_items = {
#             'name': watchlist.name,
#             'items': []
#         }

#         for watchlist_data in watchlist.watchlist_data:
#             item = {
#                 'company_name': watchlist_data.company_name,
#                 'price': watchlist_data.price
#             }
#             watchlist_items['items'].append(item)

#         watchlist_data.append(watchlist_items)

#     return render_template('index.html', watchlist_count=watchlist_count, watchlist_data=watchlist_data)

@app.route('/watchlist', methods=['GET', 'POST'])
def watchlist():
    if request.method == 'POST':
        # Handle the creation of watchlist items
        user_id = current_user.id
        user = User.query.get(int(user_id))
        watchlist_count = len(user.watchlists) + 1
        watchlist_name = f"Watchlist {watchlist_count}"

        # Create a new watchlist for the user
        watchlist = Watchlist(name=watchlist_name, user=user)
        db.session.add(watchlist)
        db.session.commit()

        return jsonify({'watchlist_name': watchlist_name, 'watchlist_id': watchlist.id})

    # Handle the retrieval of watchlist data
    user_id = current_user.id
    user = User.query.get(int(user_id))
    watchlists = user.watchlists
    watchlist_count = len(user.watchlists)
    watchlist_data = []

    for watchlist in user.watchlists:
        watchlist_items = {
            'name': watchlist.name,
            'items': []
        }

        for watchlist_data_item in watchlist.watchlist_data:
            item = {
                'company_name': watchlist_data_item.company_name,
                'price': watchlist_data_item.price
            }
            watchlist_items['items'].append(item)

        watchlist_data.append(watchlist_items)

    return render_template('index.html', watchlist_count=watchlist_count, watchlist_data=watchlist_data, watchlists=watchlists)



@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.pwd, form.pwd.data):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Invalid Username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template("auth.html",
        form=form,
        text="Login",
        title="Login",
        btn_action="Login"
        )



# Register route
@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()
    if form.validate_on_submit():
        try:
            email = form.email.data
            pwd = form.pwd.data
            username = form.username.data
            
            newuser = User(
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
            )
    
            db.session.add(newuser)
            db.session.commit()
            flash(f"Account Succesfully created", "success")
            return redirect(url_for("login"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "danger")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "danger")
    return render_template("auth.html",
        form=form,
        text="Create account",
        title="Register",
        btn_action="Register account"
        )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
