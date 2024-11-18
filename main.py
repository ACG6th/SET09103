from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from urllib.parse import unquote
import dotenv #secure private info from .env file

env = dotenv.dotenv_values(".env")

# Create the Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' #have user's info saved
db = SQLAlchemy(app) #create a db with sqlalchemy
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Replace with my Spoonacular API key
API_KEY = env.get("API_KEY")

# User model for database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Create tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        flash('Invalid username or password', 'error')
    return render_template('login.html') #returns back to login

# Route for registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
        else:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user) #add user to database
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Route for logging out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

# Define the route for the "Home" button
@app.route('/home', methods=['GET'])
@login_required
def home():
    return render_template('index.html', recipes=[], search_query='')

# Define the main route for the app
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        query = request.form.get('search_query', '')
        recipes = search_recipes(query)
        return render_template('index.html', recipes=recipes, search_query=query)

    search_query = request.args.get('search_query', '')
    decoded_search_query = unquote(search_query)
    recipes = search_recipes(decoded_search_query)
    return render_template('index.html', recipes=recipes, search_query=decoded_search_query)

# Function to search for recipes
def search_recipes(query):
    url = 'https://api.spoonacular.com/recipes/complexSearch'
    params = {
        'apiKey': API_KEY,
        'query': query,
        'number': 10,
        'instructionsRequired': True,
        'addRecipeInformation': True,
        'fillIngredients': True,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data['results']
    return []

# Route to view a specific recipe with a given recipe ID
@app.route('/recipe/<int:recipe_id>')
@login_required
def view_recipe(recipe_id):
    search_query = request.args.get('search_query', '')
    url = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
    params = {'apiKey': API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        recipe = response.json()
        return render_template('view_recipe.html', recipe=recipe, search_query=search_query)
    return "Recipe not found", 404


if __name__ == '__main__':
    app.run(debug=True)
